#!/usr/bin/python3
import re
from os import listdir
from os.path import join, isfile
from pickle import load, dump
import urllib.request

""" Generates ietf.bib with all IETF bibtex entries

This files reads tex files and lists the bib keys stored in
\cite{bib_key}. References that are related to IETF (rfc and drafts)
are extracted and the corresponding bibtex entries are put into
ietf.bib. This file can be used by bibtex

Example:
    In the directory that contains all the tex files with the IETF
    references. Type:
    
        $ ./bib_ietf.py
    
    It generates the ietf.bib files. To consider the corresponding file
    the latex file should be like:
 
        \bibliography{bib,ietf}
    
    bib points to bib.bib ( the generic files that contains all non ietf
    bibtentires) and ietf.bib that is generated here and that contains the
    IETF related bib entries. 

    The typical commands are:
    
        $ pdflatex paper.tex
        $ pdflatex paper.tex
        $ bib_ietf.py 
        $ bibtex paper.aux
        $ pdflatex paper.tex 

"""
class BibEntry:
    """ defines generic function for a bibtex key

    Args:
      bib_key (str): the key used in the tex file to designate the
        bibtex entry. It appears as \cite{bib_key} in the text file.

    Attributes:
      bib_key (str): the key used in the tex file to designate the bibtex
        entry. It typically appears in the tex file as \cite{bib_key}
      bibtex_file_key (str): the key used in the original bibtex file.
        Multiple bib_key format may be used and designate the same bibtex
        file. The bibtex file is identified by the bibtex_file_key. We
        use this element to detect duplication, that is two different
        bib_key are associated to the same bibtex entries. Typically it
        will detect that \cite{RFCXXXX} and \cite{rfcXXXX} have been
        used and will not create two different entries in the reference.
      bibtex_data (str): the bibtex_data. The bibtex_data is processed to
        match the bib_key. That is the bibtex_file_key has been replaced
        by the bib_key.
    """

    def __init__(self, bib_key):
        self.bib_key = bib_key.strip()
        self.bibtex_file_key = None
        self.bibtex_data = None

    def is_rfc(self):
        """ Evaluate a bib_key is an rfc bib_key

        Args:
          bib_key (str): the bib_key to evaluate

        Return:
          True/False (bool): if bib_key is a rfc bib_key
        """

        rfc_prefix = ["rfc", "RFC"]

        for prefix in rfc_prefix:
            if self.bib_key[: len(prefix)] != prefix:
                continue
            if len(self.bib_key) != 7:
                continue
            try:
                int(self.bib_key[3:7])
                return True
            except ValueError:
                continue
        return False

    def is_draft(self):
        """ Evaluate a bib_key is a draft bib_key

        Args:
          bib_key (str): the bib_key to evaluate

        Return:
          True/False (bool): if bib_key is a draft bib_key
        """
        draft_prefix = ["I-D.", "draft-"]

        for prefix in draft_prefix:
            if self.bib_key[:len(prefix)] == prefix:
                return True
        return False

    def download_bibtex(self, url):
        """ downloads the bibtex file at url

        Args:
          url (str): the url of the bibtex file.

        Returns:
          data (str): the output string of the url, the bibtex entry.
        """
        print("url: %s"%url)
        response = urllib.request.urlopen(url)
        data = response.read()
        return data.decode('utf-8')

    def set_bibtex_data(self, bibtex_data):
        """ update bibtex file content to the context

        Mostl likely the bib_key used in the tex file and the
        bibtex_file_key in the bibtex file do not match. This
        function replaces the bibtex_File_key with the bib_key.

        Args:
            bibtex_data (str): the content of the bibtex file.

        """
        #bibtex_key_re = re.compile(r'@techreport\{([^,]*),')
        bibtex_key_re = re.compile(r'@[a-z]*\{([^,]*),')
        self.bibtex_file_key = re.findall(bibtex_key_re, bibtex_data)[0]
        print("bibtex_data: %s"%bibtex_data)
        print("bibtex_file_key: %s"%self.bibtex_file_key)
        print("bib_key: %s"%self.bib_key)
        self.bibtex_data = bibtex_data.replace(self.bibtex_file_key, self.bib_key)


class RfcBibEntry(BibEntry):
    """ Bibtex entry for a RFC

    Args:
        bib_key (str): the key in the tex file that identify the bibtex
            entry. This is typically stored as \cite{bib_key}. The
            bib_key for an RFC is composed of a prefix ("RFC" or "rfc"
            and an id (the RFC number)
        prefix (str): designates the RFC in the bib_key. Typical values

    Parameters:
        bib_key (str): the key in the tex file that identify the bibtex
            entry. This is typically stored as \cite{bib_key}. The
            bib_key for an RFC is composed of a prefix ("RFC" or "rfc"
            and an id (the RFC number)
        prefix (str): designates the RFC in the bib_key. Typical values
            are "RFC" or "rfc"
        id (str): the RFC number
        url (str): the url to retireve the bibtex data
        bibtex_data (str): the bibtex content.
    """
    def __init__(self, bib_key):
        super().__init__(bib_key)
        if self.is_rfc() is not True:
            raise ValueError("Bad Value bib_key %s."%bib_key
                             + "Expected rfc bib_key")
        self.bib_key = bib_key.strip()
        self.prefix = self.bib_key[:3]
        self.id = self.bib_key[3:7]
        self.url = "https://datatracker.ietf.org/doc/rfc" + self.id + "/bibtex/"
        self.set_bibtex_data(self.download_bibtex(self.url))

class DraftBibEntry(BibEntry):
    """ Bibtex entry for a IETF drft

    Args:
        bib_key (str): the key in the tex file that identify the bibtex
            entry. This is typically stored as \cite{bib_key}. The
            bib_key for an IETF draft is composed of a prefix ("draft-"
            or "I-D.", an id (the name of the draft) and a version
            number.

    Parameters:
        bib_key (str): the key in the tex file that identify the bibtex
            entry. This is typically stored as \cite{bib_key}. The
            bib_key for an IETF draft is composed of a prefix ("draft-"
            or "I-D.", an id (the name of the draft) and a version
            number.
        prefix (str): designates the IETF draft in the bib_key. Typical
            values are "draft" or "I-D."
        id (str): the name of the draft
        version (str): the version number
        url (str): the url to retireve the bibtex data
        bibtex_data (str): the bibtex content.
    """
    def __init__(self, bib_key):
        super().__init__(bib_key)
        if self.is_draft() is not True:
            raise ValueError("Bad Value bib_key %s."%bib_key \
                            + "Expected draft bib_key")
        self.prefix = None
        self.id = None
        self.version = None
        self.init_bib_key()
        self.url = "https://datatracker.ietf.org/doc/draft-" + self.id + "/bibtex/"
        self.set_bibtex_data(self.download_bibtex(self.url))

    def init_bib_key(self):
        """ decompose bib_key into prefix, id and version

        """
        if self.bib_key[:4] == "I-D.":
            self.prefix = "I-D."
        elif self.bib_key[:6] == "draft-":
            self.prefix = "draft-"
        else:
            raise ValueError("Bad Value bib_key %s"%self.bib_key \
                             + "Unknown prefix")

        bib_key_split = self.bib_key.split('-')
        try:
            self.version = int(bib_key_split[- 1])
            self.id = self.bib_key[len(self.prefix): - len(self.version)- 1]
        except ValueError:
            self.id = self.bib_key[len(self.prefix):]
            self.version = None


class BibEntryDB:
    """ Database of bibtex entries

    Args:
        bibentry_db_file (str): the name of the file that stores persistent data
            of the database. The persistent data is stored as a
            dictionary { bib_key: RfcBibEntry, ...}

    Parameters:
        bibentry_db_file (str): the name of the file that stores persistent data
            of the database. The persistent data is stored as a
            dictionary { bib_key: RfcBibEntry, ...}
        bibentry_db (dict): a dictionary that associates the bib_key to the
            corresponding  RfcBibEntry and DraftBibEntry object. This has
            the form of { bib_key1: RfcBibEntry1, bib_key2: DraftBibEntry2 ... }
    """
    def __init__(self, bibentry_db_file=".bibtex.db"):
        self.bibentry_db_file = bibentry_db_file
        self.init_bibentry_db()

    def init_bibentry_db(self):
        """ Initalizes bibentry_db

        Returns:
            bibentry_db (dict): When possible it loads and returns the
                dictionary stored in  self.bibentry_db_file. Otherwise it returns
                an empty dictionary.
        """
        try:
            with open(self.bibentry_db_file, 'br' ) as f:
                self.bibentry_db = load(f)
        except (FileNotFoundError, EOFError):
            self.bibentry_db = {}

    def update(self, bib_objs):
        """ updates bibentry_db and store the new bibentry_db value

        Args:
            bib_objs (list): a list of RfcBibEntry or DraftBibEntry objects.
                Each object contains the bib_key.

        Updates self.bibentry_db with the new objects provided. When self.bibentry_db is
        updated, the new value of self.bibentry_db is stored in self.file_bibentry_db.
        """
        for i in bib_objs:
            try:
                self.bibentry_db[i.bib_key]
            except KeyError:
                self.bibentry_db[i.bib_key] = i
        with open(self.bibentry_db_file, 'bw') as f:
            dump(self.bibentry_db, f)

    def has(self, bib_key):
        """ check if bib_key is in  bibentry_db

        Args:
            bib_key (str): the bib_key in the tex file.

        Returns:
           status (bool): True if bib_key is a valid key, False
               otherwise.
        """
        if bib_key in self.bibentry_db.keys():
            return True
        return False

    def get(self, bib_key):
        """ returns the RfcBibEntry or DraftBibEntry associated to bib_key

        Args:
            bib_key (str): the bib_key in the tex file.

        Returns:
            obj (obj): the corresponding DraftBibEntry or RfcBibEntry
                object.
        """
        return self.bibentry_db[bib_key]


class BibtexFile:
    """ generates the ietf bib file

    Args:
        bibtex_file (str): the name of the file that contains all bibtex
            entries. By default the file is "ietf.bib.
        tex_file_list (list): the list of the tex files to consider. By
            default he list is empty [], and all tex files in teh
            directory are considered.
        bibentry_db_file (str): the file storing the persistent bibtex data

    Parameters:
        bibtex_file (str): the name of the file that contains all bibtex
            entries. By default the file is "ietf.bib.
        tex_file_list (list): the list of the tex files to consider. By
            default he list is empty [], and all tex files in teh
            directory are considered.
        bib_entry_db (obj): a BibEntryDB object that contains all bibtex
            entries.
    """
    def __init__(self, bibtex_file="ietf.bib", tex_file_list=[],\
                    bibentry_db_file=".bibentry.db"):
        self.bibtex_file = bibtex_file
        self.tex_file_list = self.init_tex_file_list(tex_file_list)
        self.bib_entry_db = BibEntryDB(bibentry_db_file)
        self.build()

    def init_tex_file_list(self, tex_file_list):
        """ initializes the list of tex files

        Returns:
            tex_file_list (list: list of tex files to look at for
                bib_key. When not explicitly provided, all tex files in
                the directory are considered
        """
        if tex_file_list == []:
            return [f for f in listdir("./") \
              if isfile(join("./", f)) and f.split(".")[-1] == "tex"]
        return tex_file_list


    def build(self):
        """ builds the bibtex file with all bibtex entries.

        """
        bib_keys = []
        for f in self.tex_file_list:
            bib_keys += self.bibkeys_from(f)
        ## removes redundancy
        bib_keys = list(set(bib_keys))
        bib_objs = []
        ## Build BibEntry objects
        for bib_key in bib_keys:
            try:
                bib_objs.append(self.bib_entry_db.get(bib_key))
            except KeyError:
                bib_entry = BibEntry(bib_key)
                if bib_entry.is_draft():
                    bib_objs.append(DraftBibEntry(bib_key))
                elif bib_entry.is_rfc():
                    bib_objs.append(RfcBibEntry(bib_key))
        self.bib_entry_db.update(bib_objs)
        ## check consistency (duplicated ref)
        for i in bib_objs:
            for j in bib_objs[bib_objs.index(i) + 1:]:
                if i.bibtex_file_key == j.bibtex_file_key:
                    raise ValueError("The same bibtexentry is identified by " +\
                    "two different entries: %s and %s. "%(i.bib_key, j.bib_key) + \
                    "Please choose one to avoid duplicated entries." +\
                    "If no duplicate entries appear in the text, you may remove " +\
                    "the database and rerun the script ( rm .bibentry.db) " )
        ## building bibtex_data and writing to file
        bibtex_data = ""
        for i in bib_objs:
            bibtex_data += i.bibtex_data + "\n\n"
        with open(self.bibtex_file, 'wt', encoding='utf8' ) as f:
            f.write(bibtex_data)

    def bibkeys_from(self, tex_file):
        """ returns bib keys of a tex file

        Args:
          tex_file (str): the tex file keys are read from

        Returns:
          ietf_keys (list): a list of bibtex keys
        """
        c = re.compile(r'\\cite\{([^\}]*)\}')
        bib_keys = []
        with open(tex_file, mode='rt', encoding='utf8', errors='ignore') as f:
            for line in f:
                cite_params = []
                cite_params += re.findall(c, line)
                for cite_param in cite_params:
                    if "," in cite_param:
                        for k in cite_param.split(","):
                            bib_keys.append( k.strip() )
                    else:
                        bib_keys.append(cite_param)
        return bib_keys


if __name__ == "__main__":
    bibtexfile = BibtexFile()
