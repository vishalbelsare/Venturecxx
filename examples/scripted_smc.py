import os
import argparse
#
import numpy
#
from venture.venturemagics.ip_parallel import MRipl
from venture.shortcuts import make_puma_church_prime_ripl
import vehicle_program as vp
import vehicle_simulator as vs
from contexts import Timer


def read_combined_frame():
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default=base_dir)
    parser.add_argument('--dataset_name', type=str, default='5_eight')
    parser.add_argument('--ground', action='store_true')
    args = parser.parse_args()
    base_dir = args.base_dir
    dataset_name = args.dataset_name
    use_noisy = not args.ground
    which_data = 'noisy' if use_noisy else 'ground'
    #
    dirname = os.path.join(base_dir, dataset_name, 'data', which_data)
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(dirname)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    return combined_frame

def get_row_iter(frame, N_rows=None):
    row_iter = None
    if N_rows is not None:
        row_iter = frame.head(N_rows).iterrows()
        pass
    else:
        row_iter = frame.iterrows()
        pass
    return row_iter

inspect_parameters_str = ' '.join([
    'additive_xy_error_std',
    'additive_heading_error_std',
    'fractional_xy_error_std',
    'fractional_heading_error_std',
    'gps_xy_error_std',
    'gps_heading_error_std',
    ])
def inspect_vars(ripl, _i=None):
    get_mean = lambda x: x if len(x.shape) == 1 else x.mean(axis=0)
    get_std = lambda x: x if len(x.shape) == 1 else x.std(axis=0)
    if _i is None:
        _i = row.i
        pass
    predict_str_and_func = [
            ('pose_%d' % _i, get_mean),
            ('pose_%d' % _i, get_std),
            ('control_%d' % _i, get_mean),
            ('(list %s)' % inspect_parameters_str, get_mean),
            ('(list %s)' % inspect_parameters_str, get_std),
            ]
    for predict_str, func in predict_str_and_func:
        value = numpy.array(ripl.predict(predict_str))
        func_value = func(value)
        print predict_str
        print func_value
        pass
    print
    pass

def infer_N_history(ripl, _i, N_history, N_infer=vp.N_infer, hypers=True):
    _is = range(int(_i))[-N_history:]
    map(ripl.infer, vp.get_infer_args(_is[0], N_infer, hypers))
    helper = lambda i: map(ripl.infer, vp.get_infer_args(i, N_infer, hypers=False))
    out = map(helper, _is[1:])
    return

N_hypers_profile = 31
N_history_gps = 1
N_history_not_gps = 1
to_assumes = []
def process_row(ripl, row, predictions=None, verbose=True):
    is_control_row = not numpy.isnan(row.Velocity)
    is_gps_row = not numpy.isnan(row.x)
    is_infer_hypers_row = row.i < N_hypers_profile
    N_history = N_history_gps if is_gps_row else N_history_not_gps
    N_infer = 1000 if (row.i < 4) or is_gps_row else 20
    #
    global to_assumes
    to_assume = vp.get_assume_dt(row.i, row.dt)
    to_assumes.append(to_assume)
    to_assume = vp.get_assume_control(row.i, row.Velocity, row.Steering)
    to_assumes.append(to_assume)
    to_assume = vp.get_assume_pose(row.i)
    to_assumes.append(to_assume)
    if is_gps_row:
        to_assume_str = '\n'.join(to_assumes)
        to_assumes = []
        ripl.execute_program(to_assume_str)
        vp.do_observe_gps(ripl, row.i, (row.x, row.y, row.heading))
        infer_N_history(ripl, row.i, N_history, N_infer, hypers=is_infer_hypers_row)
        pass
    return

def get_ripl(program, combined_frame, N_mripls, backend, use_mripl):
    ripl = None
    if use_mripl:
        ripl = MRipl(no_ripls=N_mripls, backend=backend, set_no_engines=N_mripls)
        pass
    else:
        ripl = make_puma_church_prime_ripl()
        pass
    ripl.execute_program(program)
    ripl.observe('(normal gps_xy_error_std 0.01)', 0)
    ripl.observe('(normal gps_heading_error_std 0.01)', 0)
    ripl.observe('(normal (lookup pose_0 0) 0.1)', combined_frame.irow(0).x)
    ripl.observe('(normal (lookup pose_0 1) 0.1)', combined_frame.irow(0).y)
    ripl.observe('(normal (lookup pose_0 2) 0.1)', combined_frame.irow(0).heading)
    out = map(ripl.infer, vp.get_infer_args(0, 1000, False))
    return ripl

def get_prefixed_expressions(ripl, prefix, instruction='predict'):
    is_this_instruction = lambda directive: directive['instruction'] == instruction
    def is_prefixed_directive(directive):
        expression = directive['expression']
        return isinstance(expression, str) and expression.startswith(prefix)
    get_expression = lambda directive: directive['expression']
    #
    directives = ripl.list_directives()
    filtered_directives = filter(is_this_instruction, directives)
    prefixed_directives = filter(is_prefixed_directive, filtered_directives)
    prefixed_expressions = map(get_expression, prefixed_directives)
    return list(set(prefixed_expressions))

def plot_poses(pose_dict):
    def plot_pose((figname, pose)):
        import scene_plot_utils as spu
        import pylab
        x, y, heading = map(numpy.array, zip(*pose))
        spu.plot_scene_scatter(x, y, heading)
        pylab.gca().set_xlim((-2.5, 2.5))
        pylab.gca().set_ylim((-5.0, 2.0))
        pylab.savefig(figname)
        pylab.close()
        return
    map(plot_pose, pose_dict.iteritems())
    return

def generate_pose_names(_is):
    generate_pose_name = lambda i: 'pose_' + str(i)
    return map(generate_pose_name, _is)

def get_logscores_and_poses(ripl, row_i):
    logscores = ripl.get_global_logscore()
    final_poses = ripl.predict('pose_%d' % row_i)
    cmp_on_logscore = lambda x, y: cmp(x[0], y[0])
    logscores_and_poses = sorted(zip(logscores, final_poses), cmp=cmp_on_logscore)
    return logscores_and_poses


combined_frame = read_combined_frame()
ripl = get_ripl(vp.program, combined_frame, vp.N_mripls, vp.backend,
        vp.use_mripl)
predictions = []
times = []
N_rows = 640
row_is = range(N_rows)
for row_i in row_is:
    with Timer('row %s' % row_i) as t:
        prediction = process_row(ripl, combined_frame.irow(row_i), predictions)
        pass
    times.append(t.elapsed)
    pass

#pose_names = get_predicted_pose_names(ripl)
temp = combined_frame.head(N_rows)
_is = temp[~numpy.isnan(temp.x)].i
pose_names = generate_pose_names(_is)
poses = map(ripl.predict, pose_names)
override_pose_names = generate_pose_names(range(len(pose_names)))
override_pose_names = ['blocked_' + x for x in override_pose_names]
pose_dict = dict(zip(override_pose_names, poses))
plot_poses(pose_dict)
# map(lambda x: inspect_vars(ripl, x), range(N_rows))
#process_row(ripl, combined_frame.irow(0))
