import sys

sys.path.append('./jwzthreading-0.91')

import jwzthreading as jwz
import mailbox

to_thread = []
counter=0

for message in mailbox.Maildir('~/src/botpy/data/Archives.ilike', factory=None):
    shell = jwz.make_message_from_email(message)
    shell.message = message.get_filename()
    to_thread.append(shell)
    counter += 1

threaded = jwz.thread(to_thread)
# Output
L = threaded.items()
L.sort()
for subj, container in L:
    jwz.print_container(container)

     
    

