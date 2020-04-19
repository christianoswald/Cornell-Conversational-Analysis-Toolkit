import unittest
from convokit.model import Utterance, User, Corpus

class CorpusIndexMeta(unittest.TestCase):
    def test_basic_functions(self):
        """
        Test basic meta functions
        """

        corpus1 = Corpus(utterances = [
            Utterance(id="0", text="hello world", user=User(id="alice")),
            Utterance(id="1", text="my name is bob", user=User(id="bob")),
            Utterance(id="2", text="this is a test", user=User(id="charlie")),
        ])

        first_utt = corpus1.get_utterance("0")
        first_utt.meta['hey'] = 9

        # correct class type stored
        self.assertEqual(corpus1.meta_index.utterances_index['hey'], repr(type(9)))

        # keyErrors result in None output
        self.assertRaises(KeyError, lambda: first_utt.meta['nonexistent key'])

        # test that setting a custom get still works
        self.assertEqual(first_utt.meta.get('nonexistent_key', {}), {})

    def test_key_insertion_deletion(self):
        corpus1 = Corpus(utterances = [
            Utterance(id="0", text="hello world", user=User(id="alice")),
            Utterance(id="1", text="my name is bob", user=User(id="bob")),
            Utterance(id="2", text="this is a test", user=User(id="charlie")),
        ])

        corpus1.get_utterance("0").meta['foo'] = 'bar'
        corpus1.get_utterance("1").meta['foo'] = 'bar2'
        corpus1.get_utterance("2").meta['hey'] = 'jude'

        corpus1.get_conversation(None).meta['convo_meta'] = 1

        corpus1.get_user("alice").meta['surname'] = 1.0

        self.assertEqual(corpus1.meta_index.utterances_index['foo'], str(type('bar')))
        self.assertEqual(corpus1.meta_index.conversations_index['convo_meta'], str(type(1)))
        self.assertEqual(corpus1.meta_index.users_index['surname'], str(type(1.0)))

        # test that deleting a key from an utterance removes it from the index
        del corpus1.get_utterance("2").meta['hey']
        self.assertRaises(KeyError, lambda: corpus1.meta_index.utterances_index['hey'])

        # test that deleting a key from an utterance removes it from the index and from all other objects of same type
        del corpus1.get_utterance("1").meta['foo']
        self.assertRaises(KeyError, lambda: corpus1.meta_index.utterances_index['foo'])
        self.assertRaises(KeyError, lambda: corpus1.get_utterance("0").meta["foo"])

    def test_corpus_merge_add(self):
        corpus1 = Corpus(utterances = [
            Utterance(id="0", text="hello world", user=User(id="alice")),
            Utterance(id="1", text="my name is bob", user=User(id="bob")),
            Utterance(id="2", text="this is a test", user=User(id="charlie")),
        ])

        corpus1.get_utterance("0").meta['foo'] = 'bar'
        corpus1.get_utterance("1").meta['foo'] = 'bar2'
        corpus1.get_utterance("2").meta['hey'] = 'jude'

        # test that adding separately initialized utterances with new metadata updates Index
        new_utt = Utterance(id="4", text="hello world", user=User(id="alice", meta={'donkey': 'kong'}),
                            meta={'new': 'meta'})

        new_corpus = corpus1.add_utterances([new_utt])
        self.assertTrue('new' in new_corpus.meta_index.utterances_index)
        self.assertTrue('donkey' in new_corpus.meta_index.users_index)

    def test_corpus_dump(self):
        corpus1 = Corpus(utterances = [
            Utterance(id="0", text="hello world", user=User(id="alice")),
            Utterance(id="1", text="my name is bob", user=User(id="bob")),
            Utterance(id="2", text="this is a test", user=User(id="charlie")),
        ])

        corpus1.get_utterance("0").meta['foo'] = 'bar'
        corpus1.get_utterance("1").meta['foo'] = 'bar2'
        corpus1.get_utterance("2").meta['hey'] = 'jude'

        corpus1.get_conversation(None).meta['convo_meta'] = 1

        corpus1.get_user("alice").meta['surname'] = 1.0
        corpus1.dump('test_index_meta_corpus', base_path="./")
        corpus2 = Corpus(filename="test_index_meta_corpus")

        self.assertEqual(corpus1.meta_index.utterances_index, corpus2.meta_index.utterances_index)
        self.assertEqual(corpus1.meta_index.users_index, corpus2.meta_index.users_index)
        self.assertEqual(corpus1.meta_index.conversations_index, corpus2.meta_index.conversations_index)
        self.assertEqual(corpus1.meta_index.overall_index, corpus2.meta_index.overall_index)

if __name__ == '__main__':
    unittest.main()
