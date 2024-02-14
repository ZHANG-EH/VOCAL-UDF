import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd
import numpy as np
import os
from time import time
from pandas.testing import assert_frame_equal
from duckdb_dir.udf import register_udf
import yaml
from vocaludf.utils import duckdb_execute_cache_sequence, duckdb_execute_clevrer_cache_sequence, duckdb_execute_clevrer_dataframe
from src.utils import program_to_dsl, dsl_to_program

config = yaml.safe_load(open("/home/enhao/VOCAL-UDF/configs/config.yaml", "r"))

def test_table_as_input():
    def test_udf(o1: dict, o2: dict) -> bool:
        return o1["color"] == 'red' and o2["color"] == 'red'

    conn = duckdb.connect()
    conn.execute("CREATE TABLE Obj_clevrer (oid INT, vid INT, fid INT, shape varchar, color varchar, material varchar, x1 float, y1 float, x2 float, y2 float)")
    conn.execute("COPY Obj_clevrer FROM '{}' (FORMAT 'csv', delimiter ',', header 0)".format(os.path.join(config["db_dir"], "obj_clevrer.csv")))
    conn.create_function("test_udf", test_udf)
    print("start")
    res = conn.execute("SELECT * FROM Obj_clevrer o1, Obj_clevrer o2 WHERE o1.vid < 100 AND o1.vid = o2.vid AND o1.fid = o2.fid AND o1.oid <> o2.oid AND test_udf(o1, o2) = true LIMIT 10").df()
    print(res.to_string())

def test_duckdb_execute_clevrer():
    conn = duckdb.connect()
    conn.execute("CREATE TABLE Obj_clevrer (oid INT, vid INT, fid INT, shape varchar, color varchar, material varchar, x1 float, y1 float, x2 float, y2 float)")
    conn.execute("COPY Obj_clevrer FROM '{}' (FORMAT 'csv', delimiter ',', header 0)".format(os.path.join(config["db_dir"], "obj_clevrer.csv")))
    # Creating index seems to produce incorrect results
    conn.execute("CREATE INDEX IF NOT EXISTS idx_obj_clevrer ON Obj_clevrer (vid)")
    register_udf(conn)

    list_size = 72159
    memo = [{} for _ in range(list_size)]
    inputs_table_name = "Obj_clevrer"
    input_vids = 10000

    # test_query = "Color(o0, 'red'), Material(o0, 'rubber'), Top(o1), FrontOf(o0, o1); FrontOf(o1, o0); Duration((Top(o2), Left(o2)), 25)"
    # test_query = "Duration((FrontOf(o0, o1), LeftOf(o1, o2), LeftOf(o2, o1), Top(o2)), 10); Duration((Color(o2, 'gray'), Material(o1, 'rubber')), 5); Duration(LeftOf(o0, o1), 15)" # 718s
    test_query = "Duration((Color(o0, 'red'), FrontOf(o1, o2), LeftOf(o2, o0)), 15); Duration((Far(o1, o2, 3.0), LeftOf(o0, o2)), 5); (Behind(o2, o0), Material(o1, 'metal'))"
    test_program = dsl_to_program(test_query)
    _start = time()
    # outputs, new_memo = duckdb_execute_clevrer_dataframe(conn, test_program, memo, inputs_table_name, input_vids)
    outputs, new_memo = duckdb_execute_clevrer_cache_sequence(conn, test_program, memo, inputs_table_name, input_vids)
    print(sorted(outputs))
    _end = time()
    print(f"Time: {_end - _start}")


    # output_postgres_python_udf = [2, 6, 41, 83, 95, 109, 111, 114, 126, 151, 154, 163, 165, 207, 214, 223, 248, 257, 315, 317, 346, 351, 369, 406, 424, 431, 493, 501, 510, 530, 546, 555, 591, 609, 619, 632, 650, 673, 688, 697, 698, 711, 730, 734, 773, 777, 805, 808, 818, 837, 843, 868, 879, 883, 900, 906, 923, 935, 947, 948, 954, 958, 971, 987, 999, 1015, 1016, 1031, 1038, 1060, 1073, 1076, 1086, 1091, 1111, 1117, 1145, 1147, 1173, 1182, 1191, 1200, 1201, 1213, 1219, 1226, 1227, 1238, 1267, 1272, 1279, 1287, 1289, 1290, 1338, 1354, 1361, 1363, 1384, 1391, 1434, 1439, 1468, 1479, 1481, 1487, 1489, 1501, 1540, 1542, 1543, 1553, 1565, 1603, 1612, 1615, 1640, 1709, 1711, 1712, 1757, 1763, 1776, 1777, 1779, 1799, 1814, 1816, 1858, 1860, 1880, 1896, 1965, 1998, 2003, 2006, 2034, 2045, 2061, 2062, 2070, 2075, 2097, 2118, 2140, 2149, 2222, 2223, 2252, 2258, 2261, 2266, 2270, 2274, 2282, 2304, 2316, 2333, 2347, 2370, 2371, 2394, 2424, 2433, 2470, 2488, 2492, 2495, 2502, 2514, 2515, 2557, 2596, 2615, 2622, 2628, 2639, 2644, 2686, 2699, 2710, 2728, 2739, 2777, 2781, 2785, 2786, 2787, 2812, 2818, 2823, 2825, 2851, 2857, 2864, 2877, 2894, 2897, 2901, 2937, 2940, 2957, 2960, 3001, 3012, 3015, 3050, 3085, 3086, 3100, 3136, 3144, 3173, 3174, 3189, 3190, 3191, 3226, 3227, 3240, 3245, 3279, 3282, 3292, 3295, 3313, 3326, 3352, 3354, 3358, 3369, 3371, 3380, 3406, 3420, 3460, 3479, 3489, 3495, 3509, 3512, 3526, 3530, 3536, 3539, 3544, 3554, 3571, 3584, 3599, 3607, 3616, 3619, 3633, 3637, 3649, 3676, 3728, 3750, 3753, 3768, 3791, 3807, 3809, 3810, 3817, 3843, 3850, 3867, 3872, 3876, 3913, 3952, 3955, 3958, 3961, 4017, 4058, 4071, 4076, 4080, 4091, 4104, 4114, 4129, 4147, 4182, 4191, 4222, 4244, 4261, 4263, 4294, 4301, 4303, 4323, 4354, 4360, 4363, 4377, 4386, 4403, 4435, 4448, 4460, 4495, 4519, 4527, 4536, 4539, 4561, 4584, 4586, 4588, 4594, 4609, 4624, 4633, 4655, 4671, 4672, 4678, 4688, 4718, 4729, 4735, 4738, 4740, 4771, 4776, 4781, 4787, 4790, 4792, 4795, 4808, 4822, 4854, 4869, 4914, 4923, 4944, 4954, 4957, 4963, 4965, 4975, 4980, 4994, 4997, 5003, 5004, 5009, 5020, 5052, 5068, 5074, 5078, 5108, 5113, 5114, 5126, 5134, 5145, 5159, 5165, 5193, 5219, 5257, 5279, 5299, 5324, 5346, 5380, 5389, 5393, 5398, 5401, 5410, 5419, 5437, 5453, 5476, 5479, 5506, 5521, 5544, 5550, 5555, 5577, 5604, 5623, 5720, 5721, 5731, 5738, 5764, 5769, 5775, 5789, 5800, 5814, 5818, 5833, 5843, 5855, 5862, 5906, 5923, 5942, 5968, 5989, 5990, 6001, 6004, 6005, 6011, 6016, 6017, 6023, 6025, 6059, 6060, 6081, 6096, 6100, 6113, 6136, 6145, 6153, 6156, 6166, 6184, 6185, 6189, 6193, 6222, 6226, 6270, 6273, 6280, 6293, 6321, 6357, 6364, 6375, 6377, 6386, 6398, 6426, 6450, 6458, 6468, 6482, 6483, 6502, 6509, 6512, 6520, 6528, 6540, 6585, 6591, 6631, 6654, 6655, 6657, 6676, 6692, 6707, 6717, 6726, 6737, 6738, 6770, 6773, 6785, 6817, 6823, 6852, 6861, 6897, 6899, 6912, 6919, 6921, 6930, 6938, 6967, 6978, 7003, 7031, 7056, 7060, 7066, 7077, 7090, 7125, 7147, 7166, 7188, 7203, 7217, 7223, 7227, 7237, 7245, 7262, 7270, 7293, 7298, 7301, 7302, 7333, 7358, 7360, 7371, 7378, 7392, 7416, 7461, 7464, 7470, 7485, 7512, 7520, 7537, 7592, 7596, 7602, 7607, 7630, 7635, 7638, 7650, 7656, 7662, 7663, 7669, 7673, 7688, 7692, 7707, 7708, 7711, 7733, 7742, 7768, 7783, 7794, 7816, 7853, 7889, 7902, 7926, 7931, 7946, 7954, 7962, 7965, 7967, 7987, 7990, 7991, 8000, 8005, 8016, 8020, 8056, 8057, 8078, 8121, 8131, 8133, 8171, 8194, 8248, 8256, 8273, 8276, 8290, 8294, 8309, 8325, 8340, 8353, 8362, 8378, 8379, 8381, 8402, 8407, 8423, 8446, 8481, 8496, 8501, 8510, 8530, 8532, 8576, 8581, 8584, 8589, 8593, 8594, 8596, 8609, 8612, 8673, 8680, 8691, 8692, 8698, 8703, 8720, 8732, 8752, 8764, 8788, 8789, 8796, 8798, 8841, 8864, 8865, 8886, 8904, 8913, 8934, 8945, 8953, 8966, 8971, 8984, 8986, 8998, 9005, 9016, 9021, 9054, 9071, 9100, 9119, 9150, 9152, 9173, 9185, 9188, 9210, 9225, 9228, 9236, 9251, 9255, 9270, 9288, 9292, 9300, 9327, 9352, 9355, 9360, 9362, 9367, 9384, 9385, 9390, 9398, 9399, 9410, 9430, 9452, 9467, 9474, 9491, 9511, 9551, 9553, 9559, 9590, 9598, 9609, 9660, 9680, 9685, 9694, 9733, 9745, 9752, 9781, 9792, 9808, 9819, 9823, 9866, 9870, 9874, 9914, 9916, 9919, 9932, 9943, 9957, 9962, 9972, 9976, 9989]

if __name__ == "__main__":
    # test_duckdb_execute_clevrer()
    test_table_as_input()