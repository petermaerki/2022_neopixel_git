#include <string.h>

// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"

// #include "py/obj.h"
// #include "py/binary.h"
#include "py/objarray.h"
#include "py/objtuple.h"

#define min(a, b) (((a) < (b)) ? (a) : (b))
#define max(a, b) (((a) > (b)) ? (a) : (b))

#if !defined(__linux__)
void *memset(void *s, int c, size_t n)
{
    return mp_fun_table.memset_(s, c, n);
}
#endif

#define LENGTH_M 5
#define COLORS 3
#define LED_PER_M 96
#define BUF_LENGTH (COLORS * LED_PER_M * LENGTH_M)
int16_t buf[BUF_LENGTH];

STATIC mp_obj_t array_int_clear(mp_obj_t self_in, mp_obj_t value_obj)
{
    memset((byte *)buf, 0, sizeof(buf));

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(array_int_clear_obj, array_int_clear);

STATIC mp_obj_t array_int_pulse(size_t n_args, const mp_obj_t *args)
{
    // mp_printf(&mp_plat_print, "a i=%d\n", 42);

    // arg[0]: bytearray
    // ...

    // arg[1]: first_led_l
    int first_led_l = mp_obj_get_int(args[1]);

    // arg[2]: factor_256
    int factor_256 = mp_obj_get_int(args[2]);
    factor_256 = max(0, min(255, factor_256));

    // arg[3]: tuple_color_rgb256
    mp_obj_tuple_t *tuple_color_rgb256 = MP_OBJ_TO_PTR(args[3]);
    size_t color_len = tuple_color_rgb256->len;
    int colors_grb65536[3];
    assert(color_len == 3);
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

    for (int current_led_lc = first_led_l * color_len; current_led_lc < BUF_LENGTH; current_led_lc += color_len)
    {
        if (current_led_lc >= 0)
        {
            int waveform_256 = mp_obj_get_int(waveform_items[waveform_pos_begin_b]);

            for (size_t color_i = 0; color_i < color_len; color_i++)
            {
                int16_t value256 = (colors_grb65536[color_i] * waveform_256) / 65536;

                buf[current_led_lc + color_i] += value256;
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
    //     mp_printf(&mp_plat_print, "a i=%d buf=%d\n", i, buf[i]);
    // }

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(array_int_pulse_obj, 7, 7, array_int_pulse);

STATIC mp_obj_t array_int_copy(mp_obj_t self_in)
{
    // self is not a memoryview, so we don't need to use (& TYPECODE_MASK)
    assert((MICROPY_PY_BUILTINS_BYTEARRAY && mp_obj_is_type(self_in, &mp_type_bytearray)) || (MICROPY_PY_ARRAY && mp_obj_is_type(self_in, &mp_type_array)));

    mp_obj_array_t *bytearray = MP_OBJ_TO_PTR(self_in);

    /*
    ** Contribute negative colors to the positive ones
    */
    size_t length = min(BUF_LENGTH, bytearray->len);
    for (int i = 0; i < length; i += COLORS)
    {
        while (true)
        {
            int positive_numbers = 0;
            int negative_numbers = 0;
            for (int c = 0; c < COLORS; c++)
            {
                // mp_printf(&mp_plat_print, " i=%d, c=%d \n", i, c);
                int16_t value256 = buf[i+c];
                if (value256 >= 0)
                {
                    positive_numbers++;
                }
                else
                {
                    // mp_printf(&mp_plat_print, "negative %d %d %d->%d\n", c, buf[i + c], i + c, i + ((c + 1) % COLORS));
                    negative_numbers++;
                    buf[i + ((c + 1) % COLORS)] += value256;
                    buf[i+c] = 0;
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
        ((byte *)bytearray->items)[i] = (byte)min(255, max(0, buf[i]));
    }

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(array_int_copy_obj, array_int_copy);

STATIC mp_obj_t array_clear(mp_obj_t self_in, mp_obj_t value_obj)
{
    // self is not a memoryview, so we don't need to use (& TYPECODE_MASK)
    assert((MICROPY_PY_BUILTINS_BYTEARRAY && mp_obj_is_type(self_in, &mp_type_bytearray)) || (MICROPY_PY_ARRAY && mp_obj_is_type(self_in, &mp_type_array)));

    mp_obj_array_t *self = MP_OBJ_TO_PTR(self_in);
    int value = mp_obj_get_int(value_obj);

    size_t item_sz = 1;
    memset((byte *)self->items, value, item_sz * self->len);

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(array_clear_obj, array_clear);

STATIC mp_obj_t array_pulse(size_t n_args, const mp_obj_t *args)
{
    // mp_printf(&mp_plat_print, "a i=%d\n", 42);

    // arg[0]: bytearray
    assert((MICROPY_PY_BUILTINS_BYTEARRAY && mp_obj_is_type(args[0], &mp_type_bytearray)));
    mp_obj_array_t *bytearray = MP_OBJ_TO_PTR(args[0]);

    // arg[1]: first_led_l
    int first_led_l = mp_obj_get_int(args[1]);

    // arg[2]: factor_256
    int factor_256 = mp_obj_get_int(args[2]);
    factor_256 = max(0, min(255, factor_256));

    // arg[3]: tuple_color_rgb256
    mp_obj_tuple_t *tuple_color_rgb256 = MP_OBJ_TO_PTR(args[3]);
    size_t color_len = tuple_color_rgb256->len;
    int colors_grb65536[3];
    assert(color_len == 3);
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

    for (int current_led_lc = first_led_l * color_len; current_led_lc < (int)bytearray->len; current_led_lc += color_len)
    {
        if (current_led_lc >= 0)
        {
            int waveform_256 = mp_obj_get_int(waveform_items[waveform_pos_begin_b]);

            for (size_t color_i = 0; color_i < color_len; color_i++)
            {
                int value_256 = (colors_grb65536[color_i] * waveform_256) / 65536;

                int value256_add = ((byte *)bytearray->items)[current_led_lc + color_i] + value_256;
                value256_add = max(0, min(255, value256_add));
                ((byte *)bytearray->items)[current_led_lc + color_i] = (byte)value256_add;
            }
        }

        waveform_pos_begin_b += speed_devicer_bpl;
        if (waveform_pos_begin_b >= waveform_len)
        {
            break;
        }
    }

    return mp_const_none; // return None, as per CPython
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(array_pulse_obj, 7, 7, array_pulse);

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_clear, MP_OBJ_FROM_PTR(&array_clear_obj));
    mp_store_global(MP_QSTR_int_clear, MP_OBJ_FROM_PTR(&array_int_clear_obj));
    mp_store_global(MP_QSTR_pulse, MP_OBJ_FROM_PTR(&array_pulse_obj));
    mp_store_global(MP_QSTR_int_pulse, MP_OBJ_FROM_PTR(&array_int_pulse_obj));
    mp_store_global(MP_QSTR_int_copy, MP_OBJ_FROM_PTR(&array_int_copy_obj));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
