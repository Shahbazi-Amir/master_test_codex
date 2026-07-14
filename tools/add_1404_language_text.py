#!/usr/bin/env python3
"""Add visually reviewed English question/choice text for the 1404 exam."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/questions/computer_engineering/exam_1404.json"

DATA = {
1:("One theory holds that humans became highly ............... because evolution selected those of our forefathers who were especially good at solving problems.",["successive","concerned","passionate","intelligent"]),
2:("Is it true that the greenhouse ..............., the feared heating of the earth's atmosphere by burning coal and oil, is just another false alarm?",["effect","energy","force","warmth"]),
3:("In most people, the charitable and ............... motives operate in some reasonable kind of balance.",["obvious","high","selfish","prime"]),
4:("Whatever the immediate ............... of the Nigerian-led intervention, West African diplomats said the long-term impact of recent events in Sierra Leone would be disastrous.",["reciprocity","outcome","reversal","meditation"]),
5:("The last thing I would wish to do is to ............... a sense of ill will, deception or animosity in an otherwise idyllic environment.",["postpone","accuse","foster","divest"]),
6:("While the movie offers unsurpassed action, ............... script makes this the least of the three ‘Die Hards.’",["an auspicious","a stirring","an edifying","a feeble"]),
7:("Relations between Communist China and the Soviet Union have unfortunately begun to ............... again after a period of relative restraint in their ideological quarrel. We can only hope that common sense prevails again.",["ameliorate","deteriorate","solemnize","petrify"]),
8:("Choose the best completion for blank (8) in the cloze passage.",["to be opened","that were opening","were opened","opening"]),
9:("Choose the best completion for blank (9) in the cloze passage.",["that are now part","which now being part","now are parts","had now been parts"]),
10:("Choose the best completion for blank (10) in the cloze passage.",["The Olympic Games came to have been","The Olympic Games have come to be","The fact is the Olympic Games to be","That the Olympic Games have been"]),
11:("The underlined word ‘utilize’ in paragraph 1 is closest in meaning to ............... .",["produce","improve","employ","analyze"]),
12:("The underlined word ‘them’ in paragraph 1 refers to ............... .",["standards","network spaces","activities","network users"]),
13:("According to paragraph 1, the appearance of computer technology and the Internet in the 20th century ............... .",["fully closed the gap that once existed between technology and human intellect","in a way resulted in some new questions about their ethical dimensions","increased the gap between ethical and unethical usage of data","prevented any opportunity of unethical usage of private data"]),
14:("All of the following words are mentioned in the passage EXCEPT ............... .",["unlawful","moral","cutting-edge","honest"]),
15:("According to the passage, which of the following statements is true?",["Computer ethics was in part developed as a response to the threat posed by hackers and other intruders who do not follow ethical standards.","Extensive use of technology has decreased the risk of potentially unethical activities such as violation of individual privacy.","Hackers utilize computer ethics as an opportunity to employ computing technology and its related disciplines to their own advantage.","Computer ethics concerns the practices that govern the production of computer units in a way that does not damage the best interest either of corporations or consumers."]),
16:("The underlined word ‘required’ in paragraph 1 is closest in meaning to ............... .",["acted up","assisted","empowered","relied on"]),
17:("The invention known as the abacus was probably a ............... .",["device","formula","game","sub-discipline"]),
18:("According to paragraph 1, ............... .",["the Chinese were the first people to discover mathematical laws","early computers were able to do simple mathematical operations","unlike older tools, modern computers do not require logical operations","logical operations refer to a unique approach to manufacturing computers"]),
19:("According to paragraph 2, which of the following statements is true?",["George Scheutz coined the term ‘Difference Engine’ in 1853.","George Scheutz's machine was used for astronomical calculations.","Babbage invented the first modern computer at the beginning of the 18th century.","Babbage won the gold medal at the Exhibition of Paris for his ‘Difference Engine.’"]),
20:("The passage provides sufficient information to answer which of the following questions? I. In which country was the first computer as we think of it produced? II. In what sense were older tools similar to computers? III. How long is the distance to the planet Mars?",["Only I","Only II","I and III","I and II"]),
21:("Which of the following techniques is used in paragraph 1?",["Definition","Statistics","Cause and effect","Rhetorical question"]),
22:("According to paragraph 2, which of the following is true about Landauer?",["His ideas ultimately led to solutions for many problems of quantum computation.","His work highlighted the challenges facing the construction of efficient quantum computers.","He later admitted that the challenges facing quantum computation were negligible.","He drew attention to the impossibility of constructing quantum computers."]),
23:("What does paragraph 3 mainly discuss?",["The difficulty of constructing quantum computers","Competing models of computation using quantum technology","The last challenge to overcome in building quantum computers","Qubit efficiency and a ground-breaking solution to its optimum realization"]),
24:("According to the passage, which of the following statements is true?",["Quantum computers are particularly versatile because qubits are highly robust and efficient in diverse environmental conditions.","Shor's ideas about different computational methods were highly influential in the development of early traditional computers.","In quantum computers, qubits must be rearranged across physical architectures, and controllable as needed for algorithms to work.","Landauer was a computer manufacturer who identified many problems in the field, and his ideas paved the way for transition from classical to quantum computation."]),
25:("In which position marked by [1], [2], [3] or [4] can the following sentence best be inserted? ‘Balancing the required isolation and interaction is difficult, but after decades of research a few systems are emerging as top candidates for large-scale quantum information processing.’",["[4]","[3]","[2]","[1]"]),
}

exam = json.loads(PATH.read_text(encoding="utf-8"))
for question in exam["questions"]:
    if question["number"] in DATA:
        question["text"], question["choice_texts"] = DATA[question["number"]]
        question["content_status"] = "visually_reviewed"
PATH.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
