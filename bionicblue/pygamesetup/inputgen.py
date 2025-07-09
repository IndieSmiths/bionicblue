
from .constants import SIZE, REVERSE_KEYS_MAP

def generate_input_data(
        key_range_pairs=(),
        no_of_frames=1,
    ):

    return {

      'events_map': {},

      'key_name_to_frames_map': {

        REVERSE_KEYS_MAP[key_value]: list(range(*range_args))
        for key_value, range_args in key_range_pairs

      },

      'last_frame_index': no_of_frames,

      'mod_key_name_to_frames_map': {},
      'mouse_key_state_requests': (),
      'mouse_pos_requests': (),
      'recording_size': SIZE,
      'recording_title': 'bionicblue_arena_door'

    }

"""
{ 'events_map': { 23: [['kd', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}]],
                  41: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  44: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  45: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  48: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  50: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  53: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  55: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  71: [['ku', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}]],
                  82: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  85: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  99: [['kd', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}]],
                  101: [['ku', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}]],
                  104: [['kd', {'k': 'K_k', 'm': ('KMOD_NUM',), 's': 'KSCAN_K', 'u': 'k'}]],
                  108: [['kd', {'k': 'K_w', 'm': ('KMOD_NUM',), 's': 'KSCAN_W', 'u': 'w'}]],
                  109: [['ku', {'k': 'K_k', 'm': ('KMOD_NUM',), 's': 'KSCAN_K', 'u': 'k'}]],
                  148: [ ['kd', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}],
                         ['ku', {'k': 'K_w', 'm': ('KMOD_NUM',), 's': 'KSCAN_W', 'u': 'w'}]],
                  177: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  186: [['kd', {'k': 'K_k', 'm': ('KMOD_NUM',), 's': 'KSCAN_K', 'u': 'k'}]],
                  195: [['ku', {'k': 'K_k', 'm': ('KMOD_NUM',), 's': 'KSCAN_K', 'u': 'k'}]],
                  200: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  203: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  205: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  208: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  209: [['ku', {'k': 'K_d', 'm': ('KMOD_NUM',), 's': 'KSCAN_D', 'u': 'd'}]],
                  210: [['kd', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]],
                  213: [['ku', {'k': 'K_j', 'm': ('KMOD_NUM',), 's': 'KSCAN_J', 'u': 'j'}]]},
  'key_name_to_frames_map': { 'K_d': [ 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
                                       61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 100, 149, 150, 151, 152, 153, 154, 155, 156,
                                       157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173,
                                       174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190,
                                       191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207,
                                       208],
                              'K_j': [ 41, 42, 43, 45, 46, 47, 50, 51, 52, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
                                       67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 86, 87, 88, 89, 90,
                                       91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
                                       110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126,
                                       127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143,
                                       144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160,
                                       161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177,
                                       200, 201, 202, 205, 206, 207, 210, 211, 212],
                              'K_k': [105, 106, 107, 108, 109, 187, 188, 189, 190, 191, 192, 193, 194],
                              'K_w': [ 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                                       126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
                                       143, 144, 145, 146, 147, 148]},
  'last_frame_index': 288,
  'mod_key_name_to_frames_map': {},
  'mouse_key_state_requests': (),
  'mouse_pos_requests': (),
  'recording_size': (320, 180),
  'recording_title': 'kennedy_at_Y2025M07D05_H21M26S18'}
"""
