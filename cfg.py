from ConfigParser import ConfigParser

class MyConfigParser(ConfigParser):
    def getlist(self,section,option):
        value = self.get(section,option)
        return list(filter(None, (x.strip() for x in value.splitlines())))

    def getlistint(self,section,option):
        return [int(x) for x in self.getlist(section,option)]


def get(file):
    config = MyConfigParser()
    return config.read(file)
