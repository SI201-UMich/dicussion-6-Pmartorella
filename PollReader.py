import os
import unittest

class PollReader():
    """
    A class for reading and analyzing polling data.
    """
    def __init__(self, filename):
        """
        The constructor. Opens up the specified file, reads in the data,
        closes the file handler, and sets up the data dictionary that will be
        populated with build_data_dict().

        We have implemented this for you. You should not need to modify it.
        """

        # this is used to get the base path that this Python file is in in an
        # OS agnostic way since Windows and Mac/Linux use different formats
        # for file paths, the os library allows us to write code that works
        # well on any operating system
        self.base_path = os.path.abspath(os.path.dirname(__file__))

        # join the base path with the passed filename
        self.full_path = os.path.join(self.base_path, filename)

        # open up the file handler
        self.file_obj = open(self.full_path, 'r')

        # read in each line of the file to a list
        self.raw_data = self.file_obj.readlines()

        # close the file handler
        self.file_obj.close()

        # set up the data dict that we will fill in later
        self.data_dict = {
            'month': [],
            'date': [],
            'sample': [],
            'sample type': [],
            'Harris result': [],
            'Trump result': []
        }

    # ---------- helpers ----------

    @staticmethod
    def _as_decimal(x: float) -> float:
        """Normalize a value that might be a percent (e.g., 57.0) or a decimal (0.57) into a decimal."""
        return x / 100.0 if x > 1.0 else x

    @staticmethod
    def _parse_sample_field(cell: str):
        """
        Parse a cell like '1880 LV' (or '1,880LV') into (1880, 'LV').
        If it's already just a number, returns (number, '').
        """
        s = cell.strip()
        num_str = ''.join(ch for ch in s if ch.isdigit())
        type_str = ''.join(ch for ch in s if ch.isalpha()).upper()
        if not num_str:
            raise ValueError(f"Could not parse sample field: {cell!r}")
        return int(num_str), type_str

    # ---------- required methods ----------

    def build_data_dict(self):
        """
        Reads all of the raw data from the CSV and builds a dictionary where
        each key is the name of a column in the CSV, and each value is a list
        containing the data for each row under that column heading.
        """
        for idx, line in enumerate(self.raw_data):
            line = line.strip()
            if not line:
                continue  # skip blank lines

            # skip the header row
            if idx == 0 and 'month' in line.lower():
                continue

            parts = [p.strip() for p in line.split(',')]

            # Your CSV has 5 columns: month, date, sample_with_type, Harris result, Trump result
            if len(parts) == 5:
                month_str, date_str, sample_cell, harris_str, trump_str = parts
                sample_num, sample_type_str = self._parse_sample_field(sample_cell)
            elif len(parts) == 6:
                # supports the alternate schema too
                month_str, date_str, sample_str, sample_type_str, harris_str, trump_str = parts
                sample_num = int(sample_str)
                sample_type_str = sample_type_str.strip().upper()
            else:
                raise ValueError(f"Unexpected CSV format on line {idx+1}: {parts}")

            self.data_dict['month'].append(month_str)
            self.data_dict['date'].append(int(date_str))
            self.data_dict['sample'].append(sample_num)
            self.data_dict['sample type'].append(sample_type_str)
            self.data_dict['Harris result'].append(float(harris_str))
            self.data_dict['Trump result'].append(float(trump_str))

    def highest_polling_candidate(self):
        """
        Return the candidate with the highest single polling percentage and that percentage.
        If the maxima are equal, return EVEN.
        """
        h_vals = [self._as_decimal(x) for x in self.data_dict['Harris result']]
        t_vals = [self._as_decimal(x) for x in self.data_dict['Trump result']]
        if not h_vals or not t_vals:
            return "EVEN at 0.0%"

        h_max = max(h_vals)
        t_max = max(t_vals)
        if abs(h_max - t_max) < 1e-12:
            return f"EVEN at {h_max*100:.1f}%"
        elif h_max > t_max:
            return f"Harris {h_max*100:.1f}%"
        else:
            return f"Trump {t_max*100:.1f}%"

    def likely_voter_polling_average(self):
        """
        Calculate the average polling percentage for each candidate among likely voters.

        Returns:
            tuple: (harris_avg_decimal, trump_avg_decimal)
        """
        h_lv, t_lv = [], []
        for st, h, t in zip(self.data_dict['sample type'],
                            self.data_dict['Harris result'],
                            self.data_dict['Trump result']):
            if st.strip().upper() == 'LV':
                h_lv.append(self._as_decimal(h))
                t_lv.append(self._as_decimal(t))

        h_avg = sum(h_lv) / len(h_lv) if h_lv else 0.0
        t_avg = sum(t_lv) / len(t_lv) if t_lv else 0.0
        return h_avg, t_avg

    def polling_history_change(self):
        """
        Calculate the change in polling averages between the earliest and latest polls.

        This method calculates the average result for each candidate in the earliest 30 polls
        and the latest 30 polls, then returns the net change.

        NOTE: Your file is in reverse-chronological order (newest first). So:
          - "latest 30"  = first 30 rows after the header
          - "earliest 30" = last 30 rows
        """
        n = len(self.data_dict['Harris result'])
        if n == 0:
            return 0.0, 0.0

        # Convert to decimals in case data ever comes in as whole percents.
        h_vals = [self._as_decimal(x) for x in self.data_dict['Harris result']]
        t_vals = [self._as_decimal(x) for x in self.data_dict['Trump result']]

        k = 30 if n >= 60 else max(0, n // 2)
        if k == 0:
            return 0.0, 0.0

        # latest = first k rows, earliest = last k rows (per file order)
        latest_idx = range(0, k)
        earliest_idx = range(n - k, n)

        def avg_at(rows, series):
            rows = list(rows)
            return sum(series[i] for i in rows) / len(rows)

        h_ear = avg_at(earliest_idx, h_vals)
        t_ear = avg_at(earliest_idx, t_vals)
        h_lat = avg_at(latest_idx, h_vals)
        t_lat = avg_at(latest_idx, t_vals)

        return (h_lat - h_ear), (t_lat - t_ear)


class TestPollReader(unittest.TestCase):
    """
    Test cases for the PollReader class.
    """
    def setUp(self):
        self.poll_reader = PollReader('polling_data.csv')
        self.poll_reader.build_data_dict()

    def test_build_data_dict(self):
        self.assertEqual(len(self.poll_reader.data_dict['date']), len(self.poll_reader.data_dict['sample']))
        self.assertTrue(all(isinstance(x, int) for x in self.poll_reader.data_dict['date']))
        self.assertTrue(all(isinstance(x, int) for x in self.poll_reader.data_dict['sample']))
        self.assertTrue(all(isinstance(x, str) for x in self.poll_reader.data_dict['sample type']))
        self.assertTrue(all(isinstance(x, float) for x in self.poll_reader.data_dict['Harris result']))
        self.assertTrue(all(isinstance(x, float) for x in self.poll_reader.data_dict['Trump result']))

    def test_highest_polling_candidate(self):
        result = self.poll_reader.highest_polling_candidate()
        self.assertTrue(isinstance(result, str))
        self.assertTrue("Harris" in result)
        self.assertTrue("57.0%" in result)

    def test_likely_voter_polling_average(self):
        harris_avg, trump_avg = self.poll_reader.likely_voter_polling_average()
        self.assertTrue(isinstance(harris_avg, float))
        self.assertTrue(isinstance(trump_avg, float))
        self.assertTrue(f"{harris_avg:.2%}" == "49.34%")
        self.assertTrue(f"{trump_avg:.2%}" == "46.04%")

    def test_polling_history_change(self):
        harris_change, trump_change = self.poll_reader.polling_history_change()
        self.assertTrue(isinstance(harris_change, float))
        self.assertTrue(isinstance(trump_change, float))
        self.assertTrue(f"{harris_change:+.2%}" == "+1.53%")
        self.assertTrue(f"{trump_change:+.2%}" == "+2.07%")


def main():
    poll_reader = PollReader('polling_data.csv')
    poll_reader.build_data_dict()

    highest_polling = poll_reader.highest_polling_candidate()
    print(f"Highest Polling Candidate: {highest_polling}")
    
    harris_avg, trump_avg = self.poll_reader.likely_voter_polling_average()  # <-- if running this file directly, change to poll_reader
    print(f"Likely Voter Polling Average:")
    print(f"  Harris: {harris_avg:.2%}")
    print(f"  Trump: {trump_avg:.2%}")
    
    harris_change, trump_change = poll_reader.polling_history_change()
    print(f"Polling History Change:")
    print(f"  Harris: {harris_change:+.2%}")
    print(f"  Trump: {trump_change:+.2%}")


if __name__ == '__main__':
    # If you want to run the sample prints, fix the small name typo in main():
    # change `self.poll_reader` to `poll_reader` on that one line.
    # Or just run the tests with:
    unittest.main(verbosity=2)
