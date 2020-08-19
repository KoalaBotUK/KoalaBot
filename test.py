values = [("a", 10, ["b", "c"], [], 1, 0, False), ("b", 9, ["c", "f"], [], 1, 0, False),
                 ("c", 8, ["a", "b", "d"], [], 0, 0, False),
                 ("d", 7, ["h", "i", "j"], [], 0, 0, False), ("e", 6, ["a", "g"], [], 1, 0, False),
                 ("f", 5, ["e", "a", "g"], [], 1, 0, False),
                 ("g", 4, ["e", "f"], [], 1, 0, False), ("h", 3, ["b", "c", "d"], [], 0, 0, False),
                 ("i", 2, ["h", "j"], [], 0, 0, False),
                 ("j", 1, ["i"], [], 0, 0, False), ("k", 7, ["i"], [], 0, 0, True), ("l", 8, ["i"], [], 0, 0, True),
                 ("m", 1, ["i"], [], 0, 0, True)]


print(sum([item[1] for item in values])/len(values))

