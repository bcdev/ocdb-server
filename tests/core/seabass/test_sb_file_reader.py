import unittest

from eocdb.core.seabass.sb_file_reader import SbFileReader
from eocdb.db.db_dataset import DbDataset


class SbFileReaderTest(unittest.TestCase):

    # def test_read(self):
    #     reader = SbFileReader()
    #     data_record = reader.read("/usr/local/data/OC_DB/bio_1535713657890739/AWI/PANGAEA/SO218/archive/SO218_pigments.sb")
    #     print(data_record)

    def setUp(self):
        self.reader = SbFileReader()

    def test_parse_empty_header_missing_begin(self):
        sb_file = ['/end_header\n']

        try:
            self.reader._parse(sb_file)
            self.fail("IOError expected")
        except IOError:
            pass

    def test_parse_empty_header_missing_end(self):
        sb_file = ['/begin_header\n']

        try:
            self.reader._parse(sb_file)
            self.fail("IOError expected")
        except IOError:
            pass

    def test_parse_location_in_header(self):
        sb_file = ['/begin_header\n',
                   '/data_file_name=pro_03_04AA_L2s.dat\n',
                   '/data_type=cast\n',
                   '/data_status=preliminary\n',
                   '/experiment=LAMONT_SCS\n',
                   '!/experiment=JUN16SCS\n',
                   '/cruise=jun16scs\n',
                   '!/cruise=FK160603\n',
                   '/station=03_04\n',
                   '/north_latitude=11.713[DEG]\n',
                   '/south_latitude=11.713[DEG]\n',
                   '/west_longitude=109.587[DEG]\n',
                   '/east_longitude=109.587[DEG]\n',
                   '/delimiter=comma\n',
                   '/fields=time,depth,ED379.9,ED412.1,ED442.6,ED470.4,ED490.5,ED510.8,ED532.4,ED555.3,ED589.6,ED619.7,ED669.8,ED683.3,ED704.9,ED779.4,LU380.3,LU470.4,LU510.1,LU589.8,LU619.7,LU704.8,LU779.9,tilt,COND,Wt,pvel\n',
                   '/end_header\n',
                   '05:42:49,0.40000000,56.61060942,122.66957337,132.33737132,114.44906813,121.14584599,129.14107229,164.93812382,153.82678513,107.74022908,74.84475416,112.73332494,117.61951804,44.97546967,12.29104733,-999,-999,-999,-999,-999,-999,-999,-999,-999,-999,-999',
                   '05:42:50,0.50000000,56.90948085,115.97783666,171.51381329,100.38906060,161.96556721,113.75394300,113.36437951,77.19171621,94.68081637,74.03389812,80.24165958,92.87650441,41.91937544,7.05047058,-999,-999,-999,-999,-999,-999,-999,2.32841663,53.06609583,27.46488778,0.37780480']

        document = self.reader._parse(sb_file)
        self.assertEqual({'data_file_name': 'pro_03_04AA_L2s.dat', 'data_type': 'cast', 'data_status': 'preliminary',
                          'experiment': 'LAMONT_SCS', 'cruise': 'jun16scs', 'station': '03_04', 'delimiter': 'comma',
                          'east_longitude': '109.587[DEG]', 'west_longitude': '109.587[DEG]',
                          'north_latitude': '11.713[DEG]', 'south_latitude': '11.713[DEG]'}, document.metadata)

        self.assertEqual(27, document.attribute_count)
        self.assertEqual("time", document.attribute_names[0])
        self.assertEqual("lu470.4", document.attribute_names[17])

        self.assertEqual(2, document.record_count)
        self.assertEqual('05:42:50', document.records[1][0])
        self.assertAlmostEqual(56.90948085, document.records[1][2])
        self.assertEqual(-999, document.records[1][21])
        self.assertEqual(27, len(document.records[0]))

        self.assertEqual(1, len(document.geo_locations()))
        self.assertAlmostEqual(109.587, document.geo_locations()[0]["lon"], 8)
        self.assertAlmostEqual(11.713, document.geo_locations()[0]["lat"], 8)

    def test_parse_location_in_records(self):
        sb_file = ['/begin_header\n',
                   '/delimiter=space\n',
                   '/fields=year,month,day,hour,minute,second,lat,lon,CHL,depth\n',
                   '/end_header\n',
                    '1992 03 01 23 04 00 12.00 -110.03 0.1700 18\n',
                    '1992 03 01 23 04 00 12.00 -110.03 0.1900 29\n',
                    '1992 03 01 23 04 00 12.00 -110.03 0.4600 46\n',
                    '1992 03 01 23 04 00 12.00 -110.03 0.3600 70\n']

        document = self.reader._parse(sb_file)
        self.assertEqual({'delimiter': 'space'}, document.metadata)

        self.assertEqual(10, document.attribute_count)
        self.assertEqual("month", document.attribute_names[1])
        self.assertEqual("second", document.attribute_names[5])

        self.assertEqual(4, document.record_count)
        self.assertEqual(3, document.records[2][1])
        self.assertEqual(23, document.records[2][3])
        self.assertAlmostEqual(-110.03, document.records[2][7], 8)
        self.assertEqual(11, len(document.records[0]))  # @todo 3 tb/tb why is this 11 - we just have 10 data fields

        self.assertEqual(4, len(document.geo_locations()))
        self.assertAlmostEqual(-110.03, document.geo_locations()[1]["lon"], 8)
        self.assertAlmostEqual(12.0, document.geo_locations()[1]["lat"], 8)

    def test_parse_time_in_header(self):
        # @todo 1 tb/tb continue here 2018-09-12
        pass

    def test_extract_delimiter_regex(self):
        dataset = DbDataset()
        dataset.set_metadata({'delimiter': 'comma'})

        regex = self.reader._extract_delimiter_regex(dataset)
        self.assertEqual(",+", regex)

        dataset.set_metadata({'delimiter': 'space'})
        regex = self.reader._extract_delimiter_regex(dataset)
        self.assertEqual("\s+", regex)

        dataset.set_metadata({'delimiter': 'tab'})
        regex = self.reader._extract_delimiter_regex(dataset)
        self.assertEqual("\t+", regex)

    def test_extract_delimiter_regex_invalid(self):
        dataset = DbDataset()
        dataset.set_metadata({'delimiter': 'double-slash-and-semicolon'})

        try:
            self.reader._extract_delimiter_regex(dataset)
            self.fail("IOException expected")
        except IOError:
            pass

    def test_extract_delimiter_regex_missing(self):
        dataset = DbDataset()

        try:
            self.reader._extract_delimiter_regex(dataset)
            self.fail("IOException expected")
        except IOError:
            pass

    def test_is_number(self):
        self.assertTrue(self.reader._is_number('1246'))
        self.assertTrue(self.reader._is_number('0.2376'))
        self.assertFalse(self.reader._is_number('23:07:33'))
        self.assertFalse(self.reader._is_number('nasenmann'))

    def test_is_integer(self):
        self.assertTrue(self.reader._is_integer('1246'))
        self.assertTrue(self.reader._is_integer('-999'))
        self.assertFalse(self.reader._is_integer('0.25216'))
        self.assertFalse(self.reader._is_integer('23:07:33'))
        self.assertFalse(self.reader._is_integer('rattelschneck'))

    def test_extract_angle_value(self):
        self.assertAlmostEqual(1.7654, self.reader._extract_angle("1.7654[DEG]"), 8)
        self.assertAlmostEqual(-76.33454, self.reader._extract_angle("-76.33454[DEG]"), 8)
        self.assertAlmostEqual(0.5521, self.reader._extract_angle("0.5521"), 8)
        self.assertAlmostEqual(-2.00987, self.reader._extract_angle("-2.00987"), 8)