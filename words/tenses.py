
def readWords(fileName):
    #Reads a file storing it by lines in a string list
    list = open(fileName).readlines()
    list=[x.strip("\n").replace("	","") for x in list]
    return list

tenses = readWords("tenses.txt")

def getTense(input_verb, tense = "past"):
    irregularFlag = False
    for entry in tenses:
        entry_root = entry.split(" ")[0]
        if input_verb == entry_root:
            irregularFlag = True
            if tense == "participle":
                return_verb = entry.split(" ")[2]
            else:
                return_verb = entry.split(" ")[1]
    if not irregularFlag:
        if input_verb[-1] not in ["a","e","i","o","u",]:
            return_verb = input_verb+"ed"
        else:
            return_verb = input_verb+"d"
            
raw_input("END")