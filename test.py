

def to_string(list):
    l = []
    for x in list:
        l.append(x[0])
        l.append(x[1])
    return '\n'.join(l)

def to_tup_list(string):
    split = string.split()
    result = []
    for i in range(0, len(split), 2):
        result.append((split[i], split[i + 1]))
    return result

flash = [('test', 'hello'), ('foo', 'bar')]

string = to_string(flash)

flash = to_tup_list(string)


print(flash)


# a, b = r2()
#
# print(a, b)




if __name__ == '__main__':
    pass
