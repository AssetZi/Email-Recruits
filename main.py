from helpers import scrapeRecruits
from delong import sendDelong
from messengerBot import send_telegram

# scrapeRecruits('2028test.csv',False,'2028 Test')


scrapeRecruits('committed.csv',True, 'Committs')
scrapeRecruits('2026.csv',False, '2026')
scrapeRecruits('2027.csv',False, '2027')
scrapeRecruits('2028.csv',False, '2028')
scrapeRecruits('2029.csv',False, '2029')

sendDelong()

send_telegram('Sent the Email ✅ -- Github pull works :D')

