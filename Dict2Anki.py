#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import ssl
import time
import json
import sqlite3
import pickle
import os
import sys
from sys import platform
from os.path import expanduser
import traceback
import StringIO
# Anki
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, askUser, tooltip
# PyQT
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
reload(sys)
sys.setdefaultencoding('utf-8')
home = expanduser("~")
# detecting operating system
if platform == "linux" or platform == "linux2":
    pass
elif platform == "darwin":
    eudictDB = home + "/Library/Eudb_en/.study.dat"
    youdaoDB = home + "/Library/Containers/com.youdao.YoudaoDict/Data/Library/com.youdao.YoudaoDict/wordbook.db"
elif platform == "win32":
    ssl._create_default_https_context = ssl._create_unverified_context
    eudictDB = home + "\AppData\Roaming\Francochinois\eudic\study.db"
    youdaoDB = home + "\AppData\Local\Yodao\DeskDict\WbData\megachweng\local"


class Window(QWidget):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.initComponent()
        self.thread = None

    def initComponent(self):
        self.resize(380, 490)
        self.groupBox = QGroupBox(self)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 360, 471))
        self.groupBox.setTitle("")
        self.debug = QPlainTextEdit(self.groupBox)
        self.debug.setGeometry(QtCore.QRect(20, 160, 321, 301))
        self.line = QFrame(self.groupBox)
        self.line.setGeometry(QtCore.QRect(20, 70, 325, 31))
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.dictList = QComboBox(self.groupBox)
        self.dictList.setGeometry(QtCore.QRect(113, 50, 161, 26))
        # self.dictList.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        # self.dictList.setFrame(False)
        self.dictList.addItem("")
        self.dictList.addItem("")
        self.widget = QWidget(self.groupBox)
        self.widget.setGeometry(QtCore.QRect(20, 10, 331, 34))
        self.decksection = QHBoxLayout(self.widget)
        self.decksection.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.widget)
        self.decksection.addWidget(self.label)
        self.deckList = QComboBox(self.widget)
        self.deckList.setEditable(True)
        self.decksection.addWidget(self.deckList)
        self.syncButton = QPushButton(self.widget)
        self.decksection.addWidget(self.syncButton)
        self.decksection.setStretch(1, 1)
        self.widget1 = QWidget(self.groupBox)
        self.widget1.setGeometry(QtCore.QRect(21, 90, 321, 46))
        self.progressSection = QVBoxLayout(self.widget1)
        self.progressSection.setContentsMargins(0, 0, 0, 0)
        self.term = QProgressBar(self.widget1)
        self.term.setProperty("value", 0)
        self.progressSection.addWidget(self.term)
        self.total = QProgressBar(self.widget1)
        self.total.setProperty("value", 0)
        self.progressSection.addWidget(self.total)
        self.downloadimage = QCheckBox(self.groupBox)
        self.downloadimage.setGeometry(QtCore.QRect(18, 48, 91, 28))
        self.downloadimage.setChecked(True)
        self.detials = QPushButton(self.groupBox)
        self.detials.setGeometry(QtCore.QRect(280, 50, 72, 32))

        self.dictList.setItemText(0, "Youdao")
        self.dictList.setItemText(1, "EuDict")
        self.label.setText("Sync to")
        self.syncButton.setText("Sync")
        self.downloadimage.setText("Save image")
        self.detials.setText("Details")

        self.syncButton.clicked.connect(self.sync)

        self.getDeckNames()
        self.initDB()
        self.getSettings()
        self.show()  # shows the window

    def initDB(self):
        conn = sqlite3.connect('Dict2Anki.db')
        cursor = conn.cursor()
        cursor.execute('create table if not exists history (id INTEGER primary key, terms TEXT,time TEXT,deckname TEXT)')
        cursor.execute('create table if not exists settings (id INTEGER primary key,deckname TEXT, downloadimage INTEGER, dictname TEXT)')
        cursor.close()
        conn.commit()
        conn.close()

    def getSettings(self):
        conn = sqlite3.connect('Dict2Anki.db')
        cursor = conn.cursor()
        cursor.execute('select * from settings')
        values = cursor.fetchall()
        conn.commit()
        conn.close()
        if values:
            self.debug.appendPlainText('GetSettingsFromDatabase')
            deckname = values[0][1]
            downloadimage = ((values[0][2] == 1) and True or False)
            dictname = values[0][3]
            self.downloadimage.setChecked(downloadimage)
            if dictname == "Youdao":
                self.dictList.setCurrentIndex(0)
            elif dictname == "EuDict":
                self.dictList.setCurrentIndex(1)
            else:
                self.dictList.setCurrentIndex(-1)
                
            # self.debug.appendPlainText(str(self.dictList.findData(dictname)))
            self.debug.appendPlainText(str(dictname))
            

    def saveSettings(self):
        self.debug.appendPlainText('SaveSettings')
        deckname = self.deckList.currentText()
        downloadimage = self.downloadimage.isChecked() and 1 or 0
        dictname = self.dictList.currentText()
        self.debug.appendPlainText('Settings:{} {} {}'.format(deckname, downloadimage, dictname))

        conn = sqlite3.connect('Dict2Anki.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO settings (id,deckname,downloadimage,dictname) VALUES(?,?,?,?)', (1, deckname, downloadimage, dictname))
        cursor.execute('UPDATE settings SET deckname=?,downloadimage=?,dictname=?  WHERE id=1', (deckname, downloadimage, dictname))
        cursor.rowcount
        conn.commit()
        conn.close()

    def getDeckNames(self):
        t = self.deckList.currentText()
        self.deckList.clear()
        alldecks = mw.col.decks.allNames()
        alldecks.remove('Default')
        for deckname in alldecks:
            self.deckList.addItem(deckname)
        if t:
            self.deckList.setEditText(t)
        self.debug.appendPlainText('Get Deck Names list')

    def sync(self):
        self.debug.appendPlainText("Click Sync")
        current = self.getCurrent()
        last = self.getLast()
        comparedTerms = self.compare(current, last)
        # stop the previous thread first
        if self.thread is not None:
            self.thread.terminate()
        # download the data!
        self.thread = lookUp(self, comparedTerms['new'])
        self.thread.start()
        while not self.thread.isFinished():
            mw.app.processEvents()
        note = Note(self, self.thread.results['lookUpedTerms'], comparedTerms['deleted'])
        note.processNote(self.deckList.currentText())
        self.thread = imageDownloader(self, self.thread.results['imageUrls'])
        self.thread.start()
        self.saveCurrent(current)
        self.saveSettings()

    def getCurrent(self):
        conn = sqlite3.connect(eudictDB)
        cursor = conn.cursor()
        cursor.execute('SELECT word FROM cus_studyrate WHERE deleted = 0')
        values = cursor.fetchall()
        conn.commit()
        conn.close()
        values = sum(map(list, values), [])
        self.debug.appendPlainText("Got current terms")
        return values

    def saveCurrent(self, current):
        deckname = self.deckList.currentText()
        conn = sqlite3.connect('Dict2Anki.db')
        cursor = conn.cursor()
        cursor.execute('insert OR IGNORE into history (terms,time,deckname) values (?,?,?)', (pickle.dumps(current), time.strftime("%Y-%m-%d %H:%M:%S"), deckname))
        cursor.close()
        conn.commit()
        conn.close()
        self.debug.appendPlainText("Current words Saved")

    def getLast(self):
        deckname = self.deckList.currentText()
        conn = sqlite3.connect('Dict2Anki.db')
        cursor = conn.cursor()
        cursor.execute("select * from history where deckname='%s'order by id desc limit 0, 1" % deckname)
        values = cursor.fetchall()
        cursor.close()
        conn.close()
        self.debug.appendPlainText("Got last terms")
        # values[number of raw][0->id,1->terms,2->time]
        if values:
            terms = pickle.loads(values[0][1])
            return terms
        else:
            return False

    def compare(self, current, last):
        data = {"deleted": [], "new": []}
        if last:
            self.debug.appendPlainText("Last record exist & Do comparasion")
            for term in last:
                if term not in current:
                    data['deleted'].append(term)

            for term in current:
                if term not in last:
                    data['new'].append(term)
            self.debug.appendPlainText(json.dumps(data, indent=4))
        else:
            self.debug.appendPlainText("First sync")
            data["new"] = current

        return data


class lookUp(QThread):
    """thread that lookup terms from public API"""

    def __init__(self, window, new):
        super(lookUp, self).__init__()
        self.window = window
        self.results = {"lookUpedTerms": [], "imageUrls": []}
        self.new = new

    def run(self):
        self.window.debug.appendPlainText("looking up thread")
        for term in self.new:
            self.window.debug.appendPlainText("looking up: " + term)
            r = self.publicAPI(term)
        self.window.debug.appendPlainText("looking up thread Finished")

    def publicAPI(self, q):
        query = urllib.urlencode({"q": q})
        f = urllib2.urlopen("https://dict.youdao.com/jsonapi?{}&dicts=%7b%22count%22%3a+99%2c%22dicts%22%3a+%5b%5b%22ec%22%2c%22phrs%22%2c%22pic_dict%22%5d%2c%5b%22web_trans%22%5d%2c%5b%22fanyi%22%5d%2c%5b%22blng_sents_part%22%5d%5d%7d".format(query))
        r = f.read()
        json_result = json.loads(r)
        try:
            explains = json_result["ec"]["word"][0]["trs"][0]["tr"][0]["l"]["i"][0]
        except:
            try:
                explains = json_result["web_trans"]["web-translation"][0]["trans"][0]["value"]
            except:
                try:
                    explains = json_result["fanyi"]["tran"]
                except:
                    explains = "None"

        try:
            uk_phonetic = json_result["ec"]["word"][0]["ukphone"]
        except:
            try:
                uk_phonetic = json_result["simple"]["word"][0]["ukphone"]
            except:
                try:
                    uk_phonetic = json_result["ec"]["word"][0]["phone"]
                except:
                    uk_phonetic = "None"

        try:
            us_phonetic = json_result["ec"]["word"][0]["usphone"]
        except:
            try:
                us_phonetic = json_result["simple"]["word"][0]["usphone"]
            except:
                try:
                    us_phonetic = json_result["ec"]["word"][0]["phone"]
                except:
                    us_phonetic = "None"
        try:
            phrases = []
            phrase_explains = []
            json_phrases = json_result["phrs"]["phrs"]
            for value in json_phrases:
                phrases.append(value["phr"]["headword"]["l"]["i"])
                phrase_explains.append(value["phr"]["trs"][0]["tr"]["l"]["i"])
        except:
            phrases = [None]
            phrase_explains = [None]

        try:
            sentences = []
            sentences_explains = []
            json_sentences = json_result["blng_sents_part"]["sentence-pair"]
            for value in json_sentences:
                sentences.append(value["sentence-eng"])
                sentences_explains.append(value["sentence-translation"])
        except:
            sentences = [None]
            sentences_explains = [None]
        # window.progress.setValue(window.progress.value() + 1)

        try:
            img = json_result["pic_dict"]["pic"][0]["image"] + "&w=150"
            if self.window.downloadimage.isChecked():
                self.results['imageUrls'].append([img, q + ".jpg"])
                img = q
        except:
            img = None

        lookUpedTerms = {
            "term": q,
            "uk": uk_phonetic,
            "us": us_phonetic,
            "definition": explains,
            "phrases": phrases[:3],
            "phrases_explains": phrase_explains[:3],
            "sentences": sentences[:3],
            "sentences_explains": sentences_explains[:3],
            "image": img
        }
        self.results['lookUpedTerms'].append(lookUpedTerms)


class imageDownloader(QThread):
    """thread that download images of terms"""

    def __init__(self, window, imageUrls):
        super(imageDownloader, self).__init__()
        self.window = window
        self.imageUrls = imageUrls

    def run(self):
        self.window.debug.appendPlainText("Thread image downloading started")
        if not os.path.exists("Deck2Anki"):
            os.makedirs("Deck2Anki")
        for imageUrl in self.imageUrls:
            self.window.debug.appendPlainText("Download image of " + imageUrl[1])
            urllib.urlretrieve(imageUrl[0], "Deck2Anki/" + imageUrl[1])
        # "Dict2Anki/" + q + ".jpg"


class Note(object):
    def __init__(self, window, new, deleted):
        self.new = new
        self.deleted = deleted
        self.window = window

    def addCustomModel(self, name, col):
        """create a new custom model for the imported deck"""
        mm = col.models
        existing = mm.byName("Dict2Anki")
        if existing:
            return existing
        m = mm.new("Dict2Anki")
        m['css'] = """.card{font-family:arial;font-size:14px;text-align:left;color:#212121;background-color:white}.pronounce{line-height:30px;font-size:24px;margin-bottom:0;word-break:break-all}.phonetic{font-size:14px;margin-left:.2em;font-family:"lucida sans unicode",arial,sans-serif;color:#01848f}.term{vertical-align:bottom;margin-right:15px}.divider{margin:1em 0 1em 0;border-bottom:2px solid #4caf50}.phrase,.sentence{color:#01848f;padding-right:1em}tr{vertical-align:top}"""

        # add fields
        mm.addField(m, mm.newField("term"))
        mm.addField(m, mm.newField("definition"))
        mm.addField(m, mm.newField("uk"))
        mm.addField(m, mm.newField("us"))
        mm.addField(m, mm.newField("phrase0"))
        mm.addField(m, mm.newField("phrase1"))
        mm.addField(m, mm.newField("phrase2"))
        mm.addField(m, mm.newField("phrase_explain0"))
        mm.addField(m, mm.newField("phrase_explain1"))
        mm.addField(m, mm.newField("phrase_explain2"))
        mm.addField(m, mm.newField("sentence0"))
        mm.addField(m, mm.newField("sentence1"))
        mm.addField(m, mm.newField("sentence2"))
        mm.addField(m, mm.newField("sentence_explain0"))
        mm.addField(m, mm.newField("sentence_explain1"))
        mm.addField(m, mm.newField("sentence_explain2"))
        mm.addField(m, mm.newField("pplaceHolder0"))
        mm.addField(m, mm.newField("pplaceHolder1"))
        mm.addField(m, mm.newField("pplaceHolder2"))
        mm.addField(m, mm.newField("splaceHolder0"))
        mm.addField(m, mm.newField("splaceHolder1"))
        mm.addField(m, mm.newField("splaceHolder2"))
        mm.addField(m, mm.newField("image"))

        # add cards
        t = mm.newTemplate("Normal")
        t['qfmt'] = """\
            <table>
            <tr>
            <td>
            <h1 class="term">{{term}}</h1>
                <div class="pronounce">
                    <span class="phonetic">UK[{{uk}}]</span> 
                    <span class="phonetic">US[{{us}}]</span>
                </div>
                <div class="definiton">Tap To View</div>
            </td>
            <td>
                {{image}}
            </td>
            </tr>
            </table>

            <div class="divider"></div>

            <table>
                <tr><td class="phrase">{{phrase0}}</td><td>{{pplaceHolder0}}</td></tr>
                <tr><td class="phrase">{{phrase1}}</td><td>{{pplaceHolder1}}</td></tr>
                <tr><td class="phrase">{{phrase2}}</td><td>{{pplaceHolder2}}</td></tr>
            </table>
            <table>
                <tr><td class="sentence">{{sentence0}}</td><td>{{splaceHolder0}}</td></tr>
                <tr><td class="sentence">{{sentence1}}</td><td>{{splaceHolder1}}</td></tr>
                <tr><td class="sentence">{{sentence2}}</td><td>{{splaceHolder2}}</td></tr>
            </table>
        """
        t['afmt'] = """\
            <table>
            <tr>
            <td>
            <h1 class="term">{{term}}</h1>
                <div class="pronounce">
                    <span class="phonetic">UK[{{uk}}]</span> 
                    <span class="phonetic">US[{{us}}]</span>
                </div>
                <div class="definiton">{{definition}}</div>
            </td>
            <td>
                {{image}}
            </td>
            </tr>
            </table>

            <div class="divider"></div>

            <table>
                <tr><td class="phrase">{{phrase0}}</td><td>{{phrase_explain0}}</td></tr>
                <tr><td class="phrase">{{phrase1}}</td><td>{{phrase_explain1}}</td></tr>
                <tr><td class="phrase">{{phrase2}}</td><td>{{phrase_explain2}}</td></tr>
            </table>
            <table>
                <tr><td class="sentence">{{sentence0}}</td><td>{{sentence_explain0}}</td></tr>
                <tr><td class="sentence">{{sentence1}}</td><td>{{sentence_explain1}}</td></tr>
                <tr><td class="sentence">{{sentence2}}</td><td>{{sentence_explain2}}</td></tr>
            </table>
        """

        mm.addTemplate(m, t)
        mm.add(m)
        self.window.debug.appendPlainText("Return template")
        return m

    def processNote(self, deckName):
        self.window.debug.appendPlainText("Processing Notes")
        deck = mw.col.decks.get(mw.col.decks.id(deckName))

        # create custom model
        model = self.addCustomModel(deckName, mw.col)

        # assign custom model to new deck
        mw.col.decks.select(deck["id"])
        mw.col.decks.get(deck)["mid"] = model["id"]
        mw.col.decks.save(deck)

        # assign new deck to custom model
        mw.col.models.setCurrent(model)
        mw.col.models.current()["did"] = deck["id"]
        mw.col.models.save(model)

        # start creating notes
        if self.new:
            for term in self.new:
                note = mw.col.newNote()
                note['term'] = term['term']
                note['definition'] = term['definition']
                note['uk'] = term['uk']
                note['us'] = term['us']
                if term['phrases'][0]:
                    for index, phrase in enumerate(term['phrases']):
                        note['phrase' + str(index)] = phrase
                        note['phrase_explain' + str(index)] = term['phrases_explains'][index]
                        note['pplaceHolder' + str(index)] = "Tap To View"
                if term['sentences'][0]:
                    for index, sentence in enumerate(term['sentences']):
                        note['sentence' + str(index)] = sentence
                        note['sentence_explain' + str(index)] = term['sentences_explains'][index]
                        note['splaceHolder' + str(index)] = "Tap To View"

                if term['image']:
                    if self.window.downloadimage.isChecked():
                        note['image'] = "<img src = 'Deck2Anki/{}.jpg'>".format(term['image'])
                    else:
                        note['image'] = "<img src ='{}' >".format(term['image'])

                mw.col.addNote(note)
            mw.col.fixIntegrity()
            mw.col.reset()
            mw.reset()
        # start deleting notes
        if self.deleted:
            self.window.debug.appendPlainText(json.dumps(self.deleted, indent=4))
            for term in self.deleted:
                cardID = mw.col.findCards("term:" + term)
                deckID = mw.col.decks.id(deckName)
                for cid in cardID:
                    nid = mw.col.db.scalar("select nid from cards where id = ? and did = ?", cid, deckID)
                    if nid is not None:
                        mw.col.db.execute("delete from cards where id =?", cid)
                        mw.col.db.execute("delete from notes where id =?", nid)
            mw.col.fixIntegrity()
            mw.col.reset()
            mw.reset()


def runYoudaoPlugin():
    try:
        """menu item pressed; display window"""
        global __window
        __window = Window()
    except Exception, e:
        traceback.print_exc(file=open('error.log', 'w+'))

# create menu item
action = QAction("Import your WordList", mw)
mw.connect(action, SIGNAL("triggered()"), runYoudaoPlugin)
mw.form.menuTools.addAction(action)