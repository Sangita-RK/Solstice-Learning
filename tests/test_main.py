import json
import unittest
from pathlib import Path

from main import answer_question
from docs_qa_utils import load_docs


ROOT = Path(__file__).resolve().parents[1]


class AnswerQuestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = load_docs(ROOT / "data" / "docs.json")
        with (ROOT / "data" / "example_questions.json").open(encoding="utf-8") as file:
            cls.examples = json.load(file)["example_questions"]

    def test_provided_supported_questions_return_source_passages(self):
        for example in self.examples:
            if example["expected_doc_id"] is None:
                continue
            with self.subTest(question=example["question"]):
                result = answer_question(example["question"], self.docs)
                self.assertEqual(result.status, "answer")
                self.assertEqual(result.doc_id, example["expected_doc_id"])
                source_doc = next(
                    doc for doc in self.docs if doc["doc_id"] == result.doc_id
                )
                self.assertIn(result.passage, source_doc["content"])

    def test_paraphrased_question_returns_supporting_passage(self):
        result = answer_question("What is the CSV export row limit?", self.docs)

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.doc_id, "D-03")
        self.assertIn("10,000 rows", result.passage)

    def test_salesforce_question_abstains(self):
        example = next(
            item for item in self.examples if item["expected_doc_id"] is None
        )

        result = answer_question(example["question"], self.docs)

        self.assertEqual(result.status, "abstain")
        self.assertIsNone(result.passage)

    def test_unmatched_specific_product_prevents_partial_answer(self):
        result = answer_question(
            "Does Salesforce support CSV exports?",
            self.docs,
        )

        self.assertEqual(result.status, "abstain")
        self.assertIsNone(result.passage)

    def test_single_generic_term_is_not_enough_evidence(self):
        result = answer_question("password", self.docs)

        self.assertEqual(result.status, "abstain")
        self.assertIsNotNone(result.message)

    def test_question_matching_multiple_settings_topics_requests_clarification(self):
        result = answer_question("What can I do in Settings?", self.docs)

        self.assertEqual(result.status, "ambiguous")
        self.assertGreaterEqual(len(result.alternatives), 2)

    def test_empty_question_abstains(self):
        self.assertEqual(answer_question("   ", self.docs).status, "abstain")


if __name__ == "__main__":
    unittest.main()
