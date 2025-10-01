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

    def build_data_dict(self):

        # skip header row
        if idx == 0 and 'month' in line.lower():
            continue

        parts = [p.strip() for p in line.split(',')]
        # expected columns: month, date, sample, sample type, Harris result, Trump result
        if len(parts) != 6:
            continue  # or raise ValueError(...) if you want to be strict

        month_str, date_str, sample_str, sample_type_str, harris_str, trump_str = parts

        self.data_dict['month'].append(month_str)
        self.data_dict['date'].append(int(date_str))
        self.data_dict['sample'].append(int(sample_str))
        self.data_dict['sample type'].append(sample_type_str)
        self.data_dict['Harris result'].append(float(harris_str))
        self.data_dict['Trump result'].append(float(trump_str))


    def highest_polling_candidate(self):
        """
        This method should iterate through the result columns and return
        the name of the candidate with the highest single polling percentage
        alongside the highest single polling percentage.
        If equal, return the highest single polling percentage and "EVEN".

        Returns:
            str: A string indicating the candidate with the highest polling percentage or EVEN,
             and the highest polling percentage.
        """
        h_vals = self.data_dict['Harris result']
        t_vals = self.data_dict['Trump result']
        if not h_vals or not t_vals:
            return "EVEN at 0.0%"

        h_max = max(h_vals)
        t_max = max(t_vals)

        # Compare maxima and format as percent
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
            tuple: A tuple containing the average polling percentages for Harris and Trump
                   among likely voters, in that order.
        """
        h_lv = []
        t_lv = []

        for st, h, t in zip(self.data_dict['sample type'],
                        self.data_dict['Harris result'],
                        self.data_dict['Trump result']):
        if st.strip().upper() == 'LV':
            h_lv.append(h)
            t_lv.append(t)

        # Avoid ZeroDivision if no LV rows (not expected, but safe)
        h_avg = sum(h_lv) / len(h_lv) if h_lv else 0.0
        t_avg = sum(t_lv) / len(t_lv) if t_lv else 0.0
        return h_avg, t_avg


    def polling_history_change(self):
        """
        Calculate the change in polling averages between the earliest and latest polls.

        This method calculates the average result for each candidate in the earliest 30 polls
        and the latest 30 polls, then returns the net change.

        Returns:
            tuple: A tuple containing the net change for Harris and Trump, in that order.
                   Positive values indicate an increase, negative values indicate a decrease.
        """
        months = self.data_dict['month']
        dates  = self.data_dict['date']
        h_vals = self.data_dict['Harris result']
        t_vals = self.data_dict['Trump result']

        if not months:
            return 0.0, 0.0

        # Map month strings to month numbers; handle both 'sep' and 'sept'
        month_order = {'aug': 8, 'sep': 9, 'sept': 9}

        idxs = list(range(len(months)))
        idxs.sort(key=lambda i: (month_order.get(months[i].strip().lower(), 99), dates[i]))

        n = len(idxs)
        k = 30 if n >= 60 else max(0, n // 2)
        if k == 0:
            return 0.0, 0.0

        earliest = idxs[:k]
        latest   = idxs[-k:]

    def avg_at(rows, series):
        return sum(series[i] for i in rows) / len(rows)

        h_ear = avg_at(earliest, h_vals)
        t_ear = avg_at(earliest, t_vals)
        h_lat = avg_at(latest,   h_vals)
        t_lat = avg_at(latest,   t_vals)

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
    
    harris_avg, trump_avg = poll_reader.likely_voter_polling_average()
    print(f"Likely Voter Polling Average:")
    print(f"  Harris: {harris_avg:.2%}")
    print(f"  Trump: {trump_avg:.2%}")
    
    harris_change, trump_change = poll_reader.polling_history_change()
    print(f"Polling History Change:")
    print(f"  Harris: {harris_change:+.2%}")
    print(f"  Trump: {trump_change:+.2%}")



if __name__ == '__main__':
    main()
    unittest.main(verbosity=2)