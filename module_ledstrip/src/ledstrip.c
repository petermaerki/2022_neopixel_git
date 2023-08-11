#include <string.h>

// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"

#include "py/objarray.h"
#include "py/objtuple.h"

#define min(a, b) (((a) < (b)) ? (a) : (b))
#define max(a, b) (((a) > (b)) ? (a) : (b))

#define COLORS 3

#if !defined(__linux__)
void *memset(void *s, int c, size_t n)
{
    return mp_fun_table.memset_(s, c, n);
}
#endif

typedef struct _mp_obj_ledstrip_t
{
    mp_obj_base_t base;
    // led_count = Led strip of 96 led3s:
    // led3_count = COLOR * led_count
    uint led_count;
    int16_t led3s[];
} mp_obj_ledstrip_t;

mp_obj_full_type_t ledstrip_type;

STATIC mp_obj_t ledstrip_init(mp_obj_t value_led_count)
{
    uint led_count = mp_obj_get_int(value_led_count);
    // mp_printf(&mp_plat_print, "led3_count=%d\n", led3_count);

    mp_obj_ledstrip_t *o = m_new_obj_var(mp_obj_ledstrip_t, int16_t, COLORS * led_count);
    o->base.type = (mp_obj_type_t *)&ledstrip_type;
    o->led_count = led_count;
    return MP_OBJ_FROM_PTR(o);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ledstrip_init_obj, ledstrip_init);

STATIC mp_obj_t ledstrip_clear(mp_obj_t self_in)
{
    mp_obj_ledstrip_t *self = MP_OBJ_TO_PTR(self_in);

    memset((byte *)self->led3s, 0, COLORS * self->led_count * sizeof(int16_t));

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ledstrip_clear_obj, ledstrip_clear);

STATIC mp_obj_t ledstrip_pulse(size_t n_args, const mp_obj_t *args)
{
    // arg[0]: bytearray
    mp_obj_ledstrip_t *self = MP_OBJ_TO_PTR(args[0]);

    // arg[1]: first_led_l
    int first_led_l = mp_obj_get_int(args[1]);

    // arg[2]: factor_256
    int factor_256 = mp_obj_get_int(args[2]);
    factor_256 = max(0, min(255, factor_256));

    // arg[3]: tuple_color_rgb256
    mp_obj_tuple_t *tuple_color_rgb256 = MP_OBJ_TO_PTR(args[3]);
    size_t color_len = tuple_color_rgb256->len;
    int colors_grb65536[3];
    assert(color_len == COLORS);
    static int rgb_2_grb[] = {1, 0, 2};
    for (size_t color_i = 0; color_i < color_len; color_i++)
    {
        colors_grb65536[color_i] = factor_256 * mp_obj_get_int(tuple_color_rgb256->items[rgb_2_grb[color_i]]);
    }

    // arg[4]: tuple_waveform256
    mp_obj_tuple_t *tuple_waveform256 = MP_OBJ_TO_PTR(args[4]);
    size_t waveform_len = tuple_waveform256->len;
    mp_obj_t *waveform_items = &tuple_waveform256->items[0];

    // arg[5]: waveform_pos_begin_b
    int waveform_pos_begin_b = mp_obj_get_int(args[5]);

    // arg[6]: speed_devicer_bpl
    int speed_devicer_bpl = mp_obj_get_int(args[6]);
    // convert to SIGNED int so the following for loop 
    int max = COLORS * self->led_count;

    for (int current_led_lc = first_led_l * color_len; current_led_lc < max; current_led_lc += color_len)
    {
        if (current_led_lc >= 0)
        {
            int waveform_256 = mp_obj_get_int(waveform_items[waveform_pos_begin_b]);

            for (size_t color_i = 0; color_i < color_len; color_i++)
            {
                int16_t value256 = (colors_grb65536[color_i] * waveform_256) / 65536;

                self->led3s[current_led_lc + color_i] += value256;
            }
        }

        waveform_pos_begin_b += speed_devicer_bpl;
        if (waveform_pos_begin_b >= waveform_len)
        {
            break;
        }
    }

    // for (int i = 0; i < 3; i++)
    // {
    //     mp_printf(&mp_plat_print, "a i=%d led3s=%d\n", i, led3s[i]);
    // }

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(ledstrip_pulse_obj, 7, 7, ledstrip_pulse);

STATIC mp_obj_t ledstrip_copy(mp_obj_t self_in, mp_obj_t obj_bytearray)
{
    mp_obj_ledstrip_t *self = MP_OBJ_TO_PTR(self_in);

    // self is not a memoryview, so we don't need to use (& TYPECODE_MASK)
    assert((MICROPY_PY_BUILTINS_BYTEARRAY && mp_obj_is_type(self_in, &mp_type_bytearray)) || (MICROPY_PY_ARRAY && mp_obj_is_type(self_in, &mp_type_array)));

    mp_obj_array_t *bytearray = MP_OBJ_TO_PTR(obj_bytearray);

    /*
    ** Contribute negative colors to the positive ones
    */
    size_t length = min(COLORS * self->led_count, bytearray->len);
    for (int i = 0; i < length; i += COLORS)
    {
        while (true)
        {
            int positive_numbers = 0;
            int negative_numbers = 0;
            for (int c = 0; c < COLORS; c++)
            {
                // mp_printf(&mp_plat_print, " i=%d, c=%d \n", i, c);
                int16_t value256 = self->led3s[i + c];
                if (value256 >= 0)
                {
                    positive_numbers++;
                }
                else
                {
                    // mp_printf(&mp_plat_print, "negative %d %d %d->%d\n", c, led3s[i + c], i + c, i + ((c + 1) % COLORS));
                    negative_numbers++;
                    // on rp2, '%' results in this error:
                    // LinkError: build/ledstrip.o: undefined symbol: __aeabi_uidivmod
                    // self->led3s[i + ((c + 1) % COLORS)] += value256;

                    int c_plus = c+1;
                    if (c_plus == COLORS)
                    {
                        c_plus = 0;
                    }
                    self->led3s[i + c_plus] += value256;
                    self->led3s[i + c] = 0;
                }
            }
            if ((negative_numbers == 0) || (positive_numbers == 0))
            {
                break;
            }
        }
    }

    for (int i = 0; i < length; i++)
    {
        ((byte *)bytearray->items)[i] = (byte)min(255, max(0, self->led3s[i]));
    }

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(ledstrip_copy_obj, ledstrip_copy);

STATIC mp_obj_t ledstrip_led_count(mp_obj_t self_in)
{
    mp_obj_ledstrip_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int(self->led_count);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ledstrip_led_count_obj, ledstrip_led_count);

mp_map_elem_t ledstrip_locals_dict_table[4];
STATIC MP_DEFINE_CONST_DICT(re_locals_dict, ledstrip_locals_dict_table);

STATIC void re_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind)
{
    (void)kind;
    mp_obj_ledstrip_t *self = MP_OBJ_TO_PTR(self_in);
    // mp_printf(print, "<re %p>", self);
    mp_printf(print, "led_count=%d", self->led_count);
}

// This is the entrv1.20.0y point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    ledstrip_type.base.type = (void *)&mp_fun_table.type_type;
    ledstrip_type.name = MP_QSTR_Ledstrip;
    MP_OBJ_TYPE_SET_SLOT(&ledstrip_type, print, re_print, 0);
    ledstrip_locals_dict_table[0] = (mp_map_elem_t){MP_OBJ_NEW_QSTR(MP_QSTR_clear), MP_OBJ_FROM_PTR(&ledstrip_clear_obj)};
    ledstrip_locals_dict_table[1] = (mp_map_elem_t){MP_OBJ_NEW_QSTR(MP_QSTR_pulse), MP_OBJ_FROM_PTR(&ledstrip_pulse_obj)};
    ledstrip_locals_dict_table[2] = (mp_map_elem_t){MP_OBJ_NEW_QSTR(MP_QSTR_copy), MP_OBJ_FROM_PTR(&ledstrip_copy_obj)};
    ledstrip_locals_dict_table[3] = (mp_map_elem_t){MP_OBJ_NEW_QSTR(MP_QSTR_led_count), MP_OBJ_FROM_PTR(&ledstrip_led_count_obj)};
    MP_OBJ_TYPE_SET_SLOT(&ledstrip_type, locals_dict, (void*)&re_locals_dict, 1);

    mp_store_global(MP_QSTR_Ledstrip, MP_OBJ_FROM_PTR(&ledstrip_init_obj));
    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}


