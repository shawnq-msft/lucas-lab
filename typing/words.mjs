// Familiar, short everyday English: function words, home, school, food and play.
const baseWords = [...new Set(`
a an the this that these those it its he she we you they me him her us them my your his our their
is am are was were be been being have has had do does did can could will would shall should may might must
and or but so if as of to in on at by for from with about into over under up down out off near far here there
not no yes all any some each every both few more most much many other same such only own very too also just now then when where why how what who which
one two three four five six seven eight nine ten first last next once twice
cat dog bird fish duck hen cow pig horse sheep goat mouse rabbit frog bear lion tiger panda monkey fox wolf deer ant bee bug fly moth
sun moon star sky cloud rain snow wind storm ice fire air water earth sea lake river beach hill rock sand mud tree leaf grass flower plant seed wood stone
red blue green yellow black white pink brown orange purple gray gold silver
big small little large long short tall high low old new young good bad nice great best happy sad glad kind fine fun funny brave calm quiet loud quick slow fast easy hard soft warm hot cool cold wet dry clean dirty dark bright light heavy full empty round flat
mum mom dad baby boy girl man woman child sister brother mother father family friend people teacher student team class
home house room door window wall floor roof bed chair table desk lamp clock box bag key cup glass plate bowl spoon fork knife pan pot bottle
book pen pencil paper page card letter word name story song game toy ball doll kite bike car bus train boat ship plane truck road street park shop store school town city farm zoo garden pool field
food bread rice milk egg meat beef pork chicken soup cake cookie cheese butter sugar salt honey jam apple pear peach grape lemon banana melon berry cherry corn bean pea potato tomato carrot onion salad pizza noodle fruit juice tea coffee lunch dinner snack
head hair face eye ear nose mouth tooth hand arm leg foot finger back body neck knee heart smile
shirt coat hat cap shoe sock dress skirt pants belt pocket watch ring
run walk jump swim ride read write draw paint sing dance play learn teach study spell count think know make build help work look see hear listen speak talk say tell ask answer call find give take get put keep let want need like love hate eat drink cook wash sleep wake sit stand move turn stop start open close bring buy pay sell try use show grow pick carry hold push pull cut hit throw catch kick climb drive travel visit meet send wait stay live go come went came made took saw got said left right again away today night day week year time hour minute morning evening before after early late soon always never often
rocket comet orbit planet space pilot cargo robot laser shield ocean forest rain snow lake bread jump learn friend
`.trim().split(/\s+/))];

// Selected single-word practice vocabulary from Cambridge A2 Key (KET),
// August 2025 topic lists, alongside familiar everyday words. Not an exhaustive syllabus.
// https://www.cambridgeenglish.org/Images/506886-a2-key-2020-vocabulary-list.pdf
export const ketWords = [...new Set(`
backpack fashion purse swimsuit raincoat tie glasses glove rucksack trainers blouse handbag scarf trousers boot bracelet hoodie shoes jacket shorts umbrella chain jeans uniform clothes jewellery wallet jumper suit necklace sweater earring wear
address digital laptop screen camera software download tablet telephone email envelope video chat file photograph information computer internet phone website conversation keyboard printer password online
advertisement diary magazine passport article diploma menu postcard bill message project form newspaper note textbook comic licence notebook ticket
advanced course lesson ruler beginner level biology dictionary library science blackboard mark board eraser maths studies bookshelf geography physics subject chemistry history practice homework practise classmate classroom instructions pupil test clever university coach language remember college rubber exam
actor drawing museum programme adventure disco music musician radio art news exhibition festival opera film painter cartoon singer chess guitar photography cinema piano theatre classical instrument picture competition concert laugh pop dancer
 aunt guest neighbour parent cousin grandfather daughter grandmother surname teenager grandparent grandson friendly uncle wife husband son granddaughter
chocolate vegetable hungry bake cola barbecue biscuit cooker boil cream kitchen curry delicious dessert meal breakfast dish burger steak cafeteria mushroom candy fridge omelette toast fried cereal garlic pasta waiter waitress chilli grilled picnic thirsty lemonade sauce sausage sandwich strawberry pepper
accident danger ambulance dangerous appointment dentist health sick doctor hospital stomach blood brain exercise ill tired chemist medicine toothache feel toothbrush comb fit nurse pain soap
bicycle collect hobby holidays cycling join party camp camping campsite member tent quiz
apartment furniture oven armchair cupboard curtain bathroom gate bedroom heating blanket downstairs bookcase drawer entrance carpet toilet shower sink sofa shelf towel pillow refrigerator rubbish
centimetre metre meter temperature kilo moment degree kilometre quarter gram litre liter second calendar birthday holiday weekend summer winter spring autumn tomorrow yesterday
able excellent lovely special afraid excited lucky strange alone famous strong amazing angry favourite noisy beautiful free terrible better pleasant bored pretty useful boring worried brilliant busy careful clear important interested different interesting difficult sorry unhappy ready
bank hotel stadium block elevator bookshop lift supermarket bookstore exit building factory office pharmacy castle grocery island village rainforest mountain area path bridge corner playground market motorway roundabout square restaurant
airport flight passenger suitcase explorer luggage petrol helicopter journey railway traffic repair tour tourist visitor driver engine engineer mechanic motorbike wheel station travel underground delayed straight
`.trim().split(/\s+/))];
export const commonWords = [...new Set([...baseWords,...ketWords])];
