from machine import Pin, PWM, Timer
from math import pi

class WheelController:
    def __init__(
        self, 
        dir_id: int, 
        pwm_id: int, 
        enc_id: int, 
    ) -> None:
        self.DIR_PIN = Pin(dir_id, Pin.OUT)
        self.PWM_PIN = PWM(Pin(pwm_id))
        self.PWM_PIN.freq(1000)
        self.ENC_PIN = Pin(enc_id, Pin.IN)
        self.ENC_PIN.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler=self.inc_counts)
        # Properties
        self.WHEEL_RADIUS = 0.127  # m, diameter is 10"
        self.GEAR_RATIO = 32
        self.CPR = 1024
        self.K_P = 0.2
        self.K_I = 0.
        self.K_D = 0.
        # Variables
        self.wdir = 0  # wheel direction: 1: forward
        self.enc_counts = 0
        self.prev_enc_counts = 0
        self.lin_vel = 0.
        self.duty = 0.
        self.err = 0.
        self.prev_err = 0.
        self.err_sum = 0.
        self.ref_vel = 0.
        # Linear velocity monitor timer
        self.monitor_timer = Timer()
        self.monitor_timer.init(freq=100, callback=self.mon_cb)
        # PID controller timer
        # self.controller_timer = Timer()
        # self.controller_timer.init(freq=100, callback=self.con_cb)

    def inc_counts(self, pin):
        self.enc_counts += self.wdir

    def mon_cb(self, timer):
        enc_diff = self.enc_counts - self.prev_enc_counts
        omega_m = enc_diff / self.CPR * 2 * pi * 100 # angular velocity on motor shaft (rad / s)
        omega_w = omega_m / self.GEAR_RATIO
        self.lin_vel = omega_w * self.WHEEL_RADIUS
        self.prev_enc_counts = self.enc_counts

    def con_cb(self, timer):
        self.err = self.ref_vel - self.lin_vel
        self.err_sum += self.err  # err_sum = err_sum + err
        self.err_diff = self.err - self.prev_err
        self.prev_err = self.err
        duty_inc = self.K_P * self.err + self.K_I * self.err_sum + self.K_D * self.err_diff  # Proportional, Integral, Derivative
        self.duty += duty_inc
        if self.duty > 0:  # forward
            if self.duty >= 1:
                self.duty = 0.999
            self._forward(self.duty)
        elif self.duty < 0:  # backward
            if self.duty <= -1:
                self.duty = -0.999
            self._backward(-self.duty)
        else:
            self.stop()
        if self.ref_vel == 0:
            self.dc = 0.
            self.stop()

    def set_vel(self, target_vel):
        if target_vel is not self.ref_vel:
            self.ref_vel = target_vel
            self.err_sum = 0.

    def _forward(self, duty: float = 0.0):
        assert -1.<=duty<= 1.
        self.DIR_PIN.value(0)
        self.PWM_PIN.duty_u16(int(65535 * duty))
        self.wdir = 1 

    def _backward(self, duty: float = 0.0):
        assert -1.<=duty<= 1.
        self.DIR_PIN.value(1)
        self.PWM_PIN.duty_u16(int(65535 * duty))
        self.wdir = -1 

    def _stop(self):
        self.PWM_PIN.duty_u16(0)
        self.wdir = 0 

    def halt(self):
        self._stop()
        self.wdir = 0 

# TEST
if __name__ == '__main__':
    from time import sleep
    lwh = WheelController(12, 13, 14)
    rwh = WheelController(16, 17, 18)
    for d in range(100):
        lwh._forward(duty=d/100)
        rwh._forward(duty=d/100)
        # print(lwh.enc_counts, rwh.enc_counts)
        print(lwh.lin_vel, rwh.lin_vel)
        sleep(0.04)
    for d in reversed(range(100)):
        lwh._forward(duty=d/100)
        rwh._forward(duty=d/100)
        # print(lwh.enc_counts, rwh.enc_counts)
        print(lwh.lin_vel, rwh.lin_vel)
        sleep(0.04)
    for d in range(100):
        lwh._backward(duty=d/100)
        rwh._backward(duty=d/100)
        # print(lwh.enc_counts, rwh.enc_counts)
        print(lwh.lin_vel, rwh.lin_vel)
        sleep(0.04)
    for d in reversed(range(100)):
        lwh._backward(duty=d/100)
        rwh._backward(duty=d/100)
        # print(lwh.enc_counts, rwh.enc_counts)
        print(lwh.lin_vel, rwh.lin_vel)
        sleep(0.04)

    # rwh = WheelController(5, 3, 7, 12, 13)
    # lwh.set_vel(-0.44)
    # rwh.set_vel(-0.4)
    # for _ in range(400):
    #     print(lwh.lin_vel, rwh.lin_vel)
    #     sleep(0.01)
    # for d in range(10):
    #     lwh.set_vel(d/10)
    #     rwh.set_vel(d/10)
    #     print(lwh.lin_vel, rwh.lin_vel)
    #     sleep(0.5)
    # print(lwh.lin_vel, rwh.lin_vel)
    # for d in reversed(range(10)):
    #     lwh.set_vel(d/10)
    #     rwh.set_vel(d/10)
    #     print(lwh.lin_vel, rwh.lin_vel)
    #     sleep(0.5)
    # print(lwh.lin_vel, rwh.lin_vel)
    # for d in range(10):
    #     lwh.set_vel(-d/10)
    #     rwh.set_vel(-d/10)
    #     print(lwh.lin_vel, rwh.lin_vel)
    #     sleep(0.5)
    # print(lwh.lin_vel, rwh.lin_vel)
    # for d in reversed(range(10)):
    #     lwh.set_vel(-d/10)
    #     rwh.set_vel(-d/10)
    #     print(lwh.lin_vel, rwh.lin_vel)
    #     sleep(0.5)
    # print(lwh.lin_vel, rwh.lin_vel)
    # lwh.controller_timer.deinit()
    # rwh.controller_timer.deinit()

    # lwh._stop()
    rwh._stop()
    # lwh.halt()
    rwh.halt()