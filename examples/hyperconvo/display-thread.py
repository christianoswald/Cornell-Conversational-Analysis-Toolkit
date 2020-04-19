import sys
import convokit

corpus = convokit.Corpus(filename=convokit.download("subreddit-Cornell"))
print(corpus.meta)
threads = corpus.utterance_threads(prefix_len=10, include_root=False)

def disp(thread, root, indent=0):
    print(" "*indent + thread[root].user.name + ": " +
        thread[root].text.replace("\n", " "))
    children = [k for k, v in thread.items() if v.reply_to == root]
    for child in children:
        disp(thread, child, indent=indent+4)

if len(sys.argv) > 1:
    for root in sys.argv[1:]:
        print("--- {} ---".format(root))
        disp(threads[root], root)
        print()
else:
    while True:
        print("Enter thread root ID (e.g. {}): ".format(next(iter(threads))), end="")
        root = input()
        print("--- {} ---".format(root))
        disp(threads[root], root)
        print()
