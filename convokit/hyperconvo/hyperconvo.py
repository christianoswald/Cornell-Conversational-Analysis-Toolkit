import numpy as np
import scipy.stats

from convokit.transformer import Transformer
from typing import Dict, Optional, Callable
from convokit.model import Corpus, Conversation
from .hypergraph import Hypergraph

def degree_stat_funcs(nan_val):
    # int wrapping is to convert from np.int64 to int, since np.int64 is not JSON-serializable
    return {
    "max": lambda l: int(np.max(l)),
    "argmax": lambda l: int(np.argmax(l)),
    "norm.max": lambda l: np.max(l) / np.sum(l) if np.sum(l) > 0 else 0,
    "2nd-largest": lambda l: int(np.partition(l, -2)[-2]) if len(l) > 1 else nan_val,
    "2nd-argmax": lambda l: int((-l).argsort()[1]) if len(l) > 1 else nan_val,
    "norm.2nd-largest": lambda l: np.partition(l, -2)[-2] / np.sum(l) if (len(l) > 1 and np.sum(l) > 0) else nan_val,
    "mean": np.mean,
    "mean-nonzero": lambda l: np.mean(l[l != 0]) if len(l[l != 0]) > 0 else 0,
    "prop-nonzero": lambda l: np.mean(l != 0),
    "prop-multiple": lambda l: np.mean(l[l != 0] > 1) if len(l[l !=0] > 1) > 0 else 0,
    "entropy": lambda l: scipy.stats.entropy(l) if np.sum(l) > 0 else nan_val,
    "2nd-largest / max": lambda l: np.partition(l, -2)[-2] / np.max(l) if (len(l) > 1 and np.sum(l) > 0) else nan_val
}

motif_stat_funcs = {
    "is-present": lambda l: len(l) > 0,
    "count": len
}

class HyperConvo(Transformer):
    """
    Encapsulates computation of hypergraph features for a particular
    corpus.

    fit_transform() retrieves features from the corpus conversational
    threads using retrieve_feats, and stores it in the corpus's conversations'
    meta field under the key "hyperconvo"

    Either use the features directly, or use the other transformers, threadEmbedder (https://convokit.cornell.edu/documentation/threadEmbedder.html)
    or communityEmbedder (https://convokit.cornell.edu/documentation/communityEmbedder.html) to embed threads or communities respectively in a low-dimensional
    space for further analysis or visualization.

    As features, we compute the degree distribution statistics from Table 4 of
    http://www.cs.cornell.edu/~cristian/Patterns_of_participant_interactions.html,
    for both a whole conversation and its midthread, and for indegree and
    outdegree distributions of C->C, C->c and c->c edges, as in the paper.
    We also compute the presence and count of each motif type specified in Fig 2.
    However, we do not include features making use of reaction edges, due to our
    inability to release the Facebook data used in the paper (which reaction
    edges are most naturally suited for). In particular, we do not include edge
    distribution statistics from Table 4, as these rely on the presence of
    reaction edges. We hope to implement a more general version of these
    reaction features in an upcoming release.

    :param prefix_len: Length (in number of utterances) of each thread to
            consider when constructing its hypergraph
    :param min_thread_len: Only consider threads of at least this length
    :param feat_name: feature name to store hyperconvo features under
    :param invalid_val: value to use for invalid hyperconvo features, default is np.nan
    """

    def __init__(self, prefix_len: int = 10, min_thread_len: int = 10, feat_name: str = "hyperconvo", invalid_val: float = np.nan):
        self.prefix_len = prefix_len
        self.min_thread_len = min_thread_len
        self.feat_name = feat_name
        self.invalid_val = invalid_val

    def transform(self, corpus: Corpus, selector: Optional[Callable[[Conversation], bool]] = lambda convo: True) -> Corpus:
        """
        Retrieves features from the Corpus Conversations using retrieve_feats() and annotates Conversations with this feature set

        :param corpus: Corpus object to retrieve feature information from
        :param selector: a (lambda) function that takes a Conversation and returns True / False; function selects
            conversations to be annotated with hypergraph features. By default, all conversations will be annotated.
        :return: corpus with conversations having a new meta field with the specified feature name  containing the stats generated by retrieve_feats().
        """

        convo_id_to_feats = self.retrieve_feats(corpus)

        for convo in corpus.iter_conversations():
            convo.add_meta(self.feat_name, convo_id_to_feats.get(convo.id, None))
        return corpus

    @staticmethod
    def _node_type_name(b: bool) -> str:
        """
        Helper method to get node type name (C or c)

        :param b: Bool, where True indicates node is a Hypernode
        :return: "C" if True, "c" if False
        """
        return "C" if b else "c"

    def _degree_feats(self, graph: Optional[Hypergraph] = None, name_ext: str = "") -> Dict:
        """
        Helper method for retrieve_feats().
        Generate statistics on degree-related features in a Hypergraph (G), or a Hypergraph
        constructed from provided utterances (uts)

        :param utts: utterances to construct Hypergraph from
        :param graph: Hypergraph to calculate degree features statistics from
        :param name_ext: Suffix to append to feature name
        :param exclude_id: id of utterance to exclude from Hypergraph construction
        :return: A stats dictionary, i.e. a dictionary of feature names to feature values. For degree-related features specifically.
        """

        stats = {}
        for from_hyper in [False, True]:
            for to_hyper in [False, True]:
                if not from_hyper and to_hyper: continue # skip c->C
                if from_hyper:
                    outdegrees = np.array(graph.outdegrees(from_hyper, to_hyper))
                indegrees = np.array(graph.indegrees(from_hyper, to_hyper))

                for stat, stat_func in degree_stat_funcs(self.invalid_val).items():
                    if from_hyper:
                        stats["{}[outdegree over {}->{} {}responses]".format(stat,
                                                                     HyperConvo._node_type_name(from_hyper),
                                                                     HyperConvo._node_type_name(to_hyper),
                                                                     name_ext)] = stat_func(outdegrees)

                    stats["{}[indegree over {}->{} {}responses]".format(stat,
                                                                        HyperConvo._node_type_name(from_hyper),
                                                                        HyperConvo._node_type_name(to_hyper),
                                                                        name_ext)] = stat_func(indegrees)
        return stats

    @staticmethod
    def _motif_feats(graph: Hypergraph = None, name_ext: str = "") -> Dict:
        """
        Helper method for retrieve_feats().
        Generate statistics on degree-related features in a Hypergraph (G), or a Hypergraph
        constructed from provided utterances (uts)

        :param utts: utterances to construct Hypergraph from
        :param graph: Hypergraph to calculate degree features statistics from
        :param name_ext: Suffix to append to feature name
        :param exclude_id: id of utterance to exclude from Hypergraph construction
        :return: A dictionary from a thread root id to its stats dictionary, which is a dictionary from feature names
            to feature values. For motif-related features specifically.
        """
        stats = {}
        for motif, motif_func in [
            ("reciprocity motif", graph.reciprocity_motifs),
            ("external reciprocity motif", graph.external_reciprocity_motifs),
            ("dyadic interaction motif", graph.dyadic_interaction_motifs),
            ("incoming triads", graph.incoming_triad_motifs),
            ("outgoing triads", graph.outgoing_triad_motifs)]:
            motifs = motif_func()
            for stat, stat_func in motif_stat_funcs.items():
                stats["{}[{}{}]".format(stat, motif, name_ext)] = stat_func(motifs)
        return stats

    def retrieve_feats(self, corpus: Corpus, selector: Callable[[Conversation], bool] = lambda convo: True) -> Dict[str, Dict]:
        """
        Retrieve all hypergraph features for a given corpus (viewed as a set of conversation threads).

        See init() for further documentation.

        :param corpus: target Corpus
        :param selector: (lambda) function selecting the Conversations that features should be computed for.
        :return: A dictionary from a thread root id to its stats dictionary,
            which is a dictionary from feature names to feature values. For degree-related
            features specifically.
        """

        threads_stats = dict()

        for convo in corpus.iter_conversations(selector):
            ordered_utts = convo.get_chronological_utterance_list()
            if len(ordered_utts) < self.min_thread_len: continue
            utts = ordered_utts[:self.prefix_len]
            stats = {}
            G = Hypergraph.init_from_utterances(utterances=utts)
            G_mid = Hypergraph.init_from_utterances(utterances=utts[1:]) # exclude root
            for k, v in self._degree_feats(graph=G).items(): stats[k] = v
            for k, v in HyperConvo._motif_feats(graph=G).items(): stats[k] = v
            for k, v in self._degree_feats(graph=G_mid, name_ext="mid-thread ").items(): stats[k] = v
            for k, v in HyperConvo._motif_feats(graph=G_mid, name_ext=" over mid-thread").items(): stats[k] = v
            threads_stats[convo.id] = stats
        return threads_stats

