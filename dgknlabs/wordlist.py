"""Small, hand-curated list of very common passwords and German patterns.

The list is intentionally tiny and maintained in-tree: it is a pattern
detector for the audit view, not a breach corpus.  Entries are lowercase;
matching is done on a leet-normalised, alpha-only form of the input.
"""

COMMON_PASSWORDS = frozenset(
    """
    123456 123456789 12345678 1234567 12345 1234 123123 111111 000000 654321
    121212 112233 159753 147258369 987654321 666666 7777777 888888 999999
    password passwort passwd pass passwort1 password1 password123 passwort123
    admin administrator root toor letmein welcome willkommen hallo hello hi
    qwerty qwertz azerty qwertyuiop asdfgh asdfghjkl zxcvbnm 1q2w3e4r 1q2w3e
    abc123 abcd1234 a1b2c3 qwe123 asd123 zxc123 test test123 testing
    iloveyou sunshine princess football baseball basketball soccer hockey
    dragon monkey master shadow superman batman matrix killer ninja starwars
    trustno1 whatever freedom changeme secret geheim geheim1
    sommer winter fruehling herbst sommer2024 sommer2025 winter2024 winter2025
    januar februar maerz april mai juni juli august september oktober november dezember
    montag dienstag mittwoch donnerstag freitag samstag sonntag
    bayern deutschland berlin muenchen hamburg koeln dresden stuttgart
    dogukan dogenc dgkn labs dgknlabs
    computer internet email google apple microsoft samsung huawei
    ich liebe dich liebe schatz mama papa freund familie
    mustang ferrari porsche mercedes bmw audi toyota honda
    liverpool chelsea arsenal barcelona realmadrid manchester juventus
    pokemon minecraft fortnite callofduty gamer player
    qazwsx qazwsxedc zaq12wsx poiuytrewa lkjhgfdsa mnbvcxz
    access welcome1 admin123 root123 user user123 guest guest123
    changeme123 default system oracle mysql postgres sa
    """.split()
)
