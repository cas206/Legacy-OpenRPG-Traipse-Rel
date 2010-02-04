Warhammer Fantasy Roleplay Dice Roller

Installing:
I wanted to make this as easy as possible so I created a duplicate folder structure.  The easiest way to install and pass this on is to copy the included dieroller folder into orpg directory. The copy will replace utils.py and add the wfrpg.py file to the rollers subfolder

Using:
Reckless (d10) Rec
Conservative (d10) Con
Characteristic (d8) Chr
Challenge (d8) Cha
Fortune (d6) For
Mistfortune (d6) Mis
Expertise (d6) Exp

Changes to Utils.py:
The changes made to utils.py do not corrupt the structure of the software, instead the changes increase portability. The changes made allow for a user to create a non_stdDie function inside a die roller. This function allows them to split die rolls with different letters (like 'v' or 'k' instead of 'd').

Another change is made towards the end of the file in the convertTheDieString function. The material that has been included in triple quotes contains a break that is not working. This will see a future bug fix.  Also, a new Regular Expressions compilation has been included if the first does not work. The change can be seen at the very end where [\dFf] becomes [a-zA-Z]. This change allows for dice to be given a text delimiter.

In this roller we use the second Regular Expressions compliation so that we can roll [1rec] and it will return the value of 1 Reckless roll.
