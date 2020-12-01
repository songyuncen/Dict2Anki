from .constants import MODEL_FIELDS, BASIC_OPTION, EXTRA_OPTION
import logging

logger = logging.getLogger('dict2Anki.noteManager')
try:
    from aqt import mw
    import anki
except ImportError:
    from test.dummy_aqt import mw
    from test import dummy_anki as anki


def getDeckList():
    return [deck['name'] for deck in mw.col.decks.all()]


def getWordsByDeck(deckName) -> [str]:
    notes = mw.col.findNotes(f'deck:"{deckName}"')
    words = []
    for nid in notes:
        note = mw.col.getNote(nid)
        if note.model().get('name', '').lower().startswith('dict2anki') and note['term']:
            words.append(note['term'])
    return words


def getNotes(wordList, deckName) -> list:
    notes = []
    for word in wordList:
        note = mw.col.findNotes(f'deck:"{deckName}" term:"{word}"')
        if note:
            notes.append(note[0])
    return notes


def getOrCreateDeck(deckName):
    deck_id = mw.col.decks.id(deckName)
    deck = mw.col.decks.get(deck_id)
    mw.col.decks.save(deck)
    mw.col.reset()
    mw.reset()
    return deck


def getOrCreateModel(modelName):
    model = mw.col.models.byName(modelName)
    if model:
        if set([f['name'] for f in model['flds']]) == set(MODEL_FIELDS):
            return model
        else:
            logger.warning('模版字段异常，自动删除重建')
            mw.col.models.rem(model)

    logger.info(f'创建新模版:{modelName}')
    newModel = mw.col.models.new(modelName)
    for field in MODEL_FIELDS:
        mw.col.models.addField(newModel, mw.col.models.newField(field))
    return newModel


def getOrCreateModelCardTemplate(modelObject, cardTemplateName):
    logger.info(f'添加卡片类型:{cardTemplateName}')
    existingCardTemplate = modelObject['tmpls']
    if cardTemplateName in [t.get('name') for t in existingCardTemplate]:
        return
    cardTemplate = mw.col.models.newTemplate(cardTemplateName)
    cardTemplate['qfmt'] = '''
<div class="bar head">牌组名称 : {{Deck}}
</div>
<div class="section">
<div class="expression">{{term}}<span class="voice">{{AmEPron}}</span></div>
<div class="phonetic">[{{AmEPhonetic}}]</div>
</div>
    '''
    cardTemplate['afmt'] = '''
{{FrontSide}}

<div class="bar head">释义 :
</div>
<div class="section">
<div id="definition" class="items">{{definition}}</div>
</div>
<div class="bar head">例句 :
</div>
<div class="section">
<div id="sentence" class="items">{{sentenceBack}}</div>
</div>
'''
    modelObject['css'] = '''
</style>
<style>
.card {
 font-family: helvetica, arial, sans-serif;
 font-size: 14px;
 text-align: left;
 color:#1d2129;
 background-color:#e9ebee;
}


.bar{
 border-radius: 3px;
 border-bottom: 1px solid #29487d;
 color: #fff;
 padding: 5px;
 text-decoration:none;
 font-size: 12px;
 color: #fff;
 font-weight: bold;
}

.head{
 padding-left:25px;
 background: #365899 url(_clipboard.png) no-repeat
}

.foot{
 padding-right:25px;
 text-align:right;
 background: #365899 url(_cloud.png) no-repeat right
}

.section {
 border: 1px solid;
 border-color: #e5e6e9 #dfe0e4 #d0d1d5;
 border-radius: 3px;
 background-color: #fff;
 position: relative;
 margin: 5px 0;
}

.expression{
 font-size: 45px;
 margin: 0 12px;
 padding: 10px 0 8px 0;
 border-bottom: 1px solid #e5e5e5;
}

.phonetic{
 font-size:14px;
 margin: 0 12px;
 padding: 10px 0 8px 0;
}

.items{
 border-top: 1px solid #e5e5e5;
 font-size: 16px;
 margin: 0 12px;
 padding: 10px 0 8px 0;
}

#definition{
 border-top: 0px;
 line-height: 1.2em;
}

#sentence{
 line-height: 1.2em;
}

#url a{
text-decoration:none;
font-size: 12px;
color: #fff;
font-weight: bold;
}

#definition a {
 text-decoration: none;
 padding: 1px 6px 2px 5px;
 margin: 0 5px 0 0;
 font-size: 12px;
 color: white;
 font-weight: normal;
 border-radius: 4px
}

#definition a.pos_n {
	background-color: #e3412f
}

#definition a.pos_v {
	background-color: #539007
}

#definition a.pos_a {
	background-color: #f8b002
}

#definition a.pos_r {
	background-color: #684b9d
}

#sentence b{
 font-weight:      normal;
 border-radius:    3px;
 color:            #fff;
 background-color: #666;
 padding-left:     3px;
 padding-right:    3px;
}

.voice img{
 margin-left:5px;
 width: 24px;
 height: 24px;
}
</style>
<style>
    '''
    mw.col.models.addTemplate(modelObject, cardTemplate)
    mw.col.models.add(modelObject)


def addNoteToDeck(deckObject, modelObject, currentConfig: dict, oneQueryResult: dict):
    if not oneQueryResult:
        logger.warning(f'查询结果{oneQueryResult} 异常，忽略')
        return
    modelObject['did'] = deckObject['id']

    newNote = anki.notes.Note(mw.col, modelObject)
    newNote['term'] = oneQueryResult['term']
    for configName in BASIC_OPTION + EXTRA_OPTION:
        logger.debug(f'字段:{configName}--结果:{oneQueryResult.get(configName)}')
        if oneQueryResult.get(configName):
            # 短语例句
            if configName in ['sentence', 'phrase'] and currentConfig[configName]:
                newNote[f'{configName}Front'] = '<hr/>'.join([f'<tr><td>{e.strip()}</td></tr>' for e, _ in oneQueryResult[configName]])
                newNote[f'{configName}Back'] = '<hr/>'.join([f'<tr><td>{e.strip()}<br>{c.strip()}</td></tr>' for e, c in oneQueryResult[configName]])
            # 图片
            elif configName == 'image':
                newNote[configName] = f'src="{oneQueryResult[configName]}"'
            # 释义
            elif configName == 'definition' and currentConfig[configName]:
                newNote[configName] = '<hr/>'.join(oneQueryResult[configName])
            # 发音
            elif configName in EXTRA_OPTION[:2]:
                newNote[configName] = f"[sound:{configName}_{oneQueryResult['term']}.mp3]"
            # 其他
            elif currentConfig[configName]:
                newNote[configName] = oneQueryResult[configName]

    mw.col.addNote(newNote)
    mw.col.reset()
    logger.info(f"添加笔记{newNote['term']}")
