import ast
from pathlib import Path
import threading
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'forgely.py'
module = ast.parse(SOURCE.read_text(encoding='utf8'))
node = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'LatestFrameMailbox')
namespace = {'threading': threading}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
Mailbox = namespace['LatestFrameMailbox']

class MailboxTests(unittest.TestCase):
    def test_only_newest_frame(self):
        mailbox = Mailbox()
        mailbox.publish('old', 'game', 10, 2)
        mailbox.publish('new', 'game', 20, 3)
        frame = mailbox.wait_new(0, threading.Event())
        self.assertEqual(frame[1], 'new')
        self.assertEqual(frame[0], 2)
    def test_no_duplicate_delivery(self):
        mailbox = Mailbox()
        mailbox.publish('one', 'game', 10, 2)
        self.assertIsNone(mailbox.wait_new(1, threading.Event()))
    def test_invalidation_clears_frame(self):
        mailbox = Mailbox()
        mailbox.publish('one', 'game', 10, 2)
        mailbox.invalidate('not foreground')
        self.assertIsNone(mailbox.wait_new(0, threading.Event()))

if __name__ == '__main__': unittest.main()
