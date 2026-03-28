"""Playwright test: quiz should show diverse items, not repeat the same ~10.

Starts the Django dev server, opens the Number->Word quiz, skips through
40 questions, and asserts that more than 15 unique prompts appeared.

Run:
    python -m pytest tests/test_quiz_diversity.py -v
"""

import os
import socket
import subprocess
import sys
import time
import unittest

from playwright.sync_api import sync_playwright


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class TestQuizDiversity(unittest.TestCase):
    server: subprocess.Popen
    port: int

    @classmethod
    def setUpClass(cls):
        cls.port = _free_port()
        env = {**os.environ, "DJANGO_DEBUG": "1"}
        cls.server = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", str(cls.port), "--noreload"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        for _ in range(30):
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=1):
                    break
            except OSError:
                time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=5)

    def test_quiz_shows_diverse_prompts(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{self.port}/")

            # Dismiss tutorial if visible (fresh session)
            page.evaluate("localStorage.setItem('tutorialSeen', 'true')")
            page.reload()
            page.wait_for_load_state("networkidle")

            # Wait for app JS to initialize and expose globals
            page.wait_for_function("typeof window.showSection === 'function'", timeout=10000)

            # Navigate to the Number->Word quiz
            page.evaluate("window.showSection('quiz')")
            page.wait_for_function(
                'document.getElementById("quiz-prompt").textContent !== "--"',
                timeout=10000,
            )

            seen_prompts = set()
            num_questions = 40

            for _ in range(num_questions):
                prompt = page.text_content("#quiz-prompt")
                seen_prompts.add(prompt)
                page.evaluate("window.skipQuiz()")
                # Wait for next question: NEXT_QUESTION_DELAY_MS(1800) + FADE_MS(200) + buffer
                page.wait_for_timeout(2200)

            browser.close()

        self.assertGreater(
            len(seen_prompts), 15,
            f"Only saw {len(seen_prompts)} unique prompts in {num_questions} questions: "
            f"{sorted(seen_prompts)}. Expected diverse selection.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
