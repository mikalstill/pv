__author__ = 'Michael Still <mikal@stillhq.com>'

import pv
import serial
import sys

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

pv.debug()
pv.debug_color()

port = serial.Serial('/dev/inverter', timeout=5)
#port.open()

from pv import cms
inv = cms.Inverter(port)

inv.reset()
sn = inv.discover()
if sn is None:
    print "Inverter is not connected."
    sys.exit(1)
ok = inv.register(sn)		# Associates the inverter and assigns default address
if not ok:
    print "Inverter registration failed."
    sys.exit(1)

print inv.version()

registry = CollectorRegistry()
Gauge('job_last_success_unixtime', 'Last time the pv job ran',
      registry=registry).set_to_current_time()

param_layout = inv.param_layout()
parameters = inv.parameters(param_layout)

parameter_name_map = {
    'Vpc-start': ('PV Start-up voltage (V)', 'voltage_startup'),
    'T-start':   ('Time to connect grid (Sec)', 'grid_connect_time'),
    'Vac-Min':   ('Minimum operational grid voltage', 'voltage_grid_minimum'),
    'Vac-Max':   ('Maximum operational grid voltage', 'voltage_grid_maximum'),
    'Fac-Min':   ('Minimum operational frequency', 'frequency_grid_minimum'),
    'Fac-Max':   ('Maximum operational frequency', 'frequency_grid_maximum'),
    'Zac-Max':   ('Maximum operational grid impedance', 'impedence_grid_maximum'),
    'DZac':      ('Allowable Delta Zac of operation', 'delta_zac_maximum')
}

for field in parameters:
    print "%-10s: %s" % field
    Gauge(parameter_name_map[field[0]][1], parameter_name_map[field[0]][0],
          registry=registry).set(field[1])

status_layout = inv.status_layout()
status = inv.status(status_layout)

status_name_map = {
    'Temp-inv':	('Inverter internal temperature (deg C)', 'temp_c'),
    'Vpv1':     ('PV1 Voltage (V)', 'voltage_pv1'),
    'Vpv2':     ('PV2 Voltage (V)', 'voltage_pv2'),
    'Vpv3':     ('PV3 Voltage (V)', 'voltage_pv3'),
    'Ipv1':     ('PV1 Current (A)', 'current_pv1'),
    'Ipv2':     ('PV2 Current (A)', 'current_pv2'),
    'Ipv3':     ('PV3 Current (A)', 'current_pv3'),
    'Vpv':      ('PV Voltage (V)', 'voltage_pv'),
    'Iac':      ('Current to grid (A)', 'current_to_grid'),
    'Vac':      ('Grid voltage (V)', 'voltage_grid'),
    'Fac':      ('Grid frequency (Hz)', 'frequency_grid'),
    'Pac':      ('Power to grid (W)', 'watts_grid'),
    'Zac':      ('Grid impedance (mOhm)', 'impedance_grid'),
    'E-Total':  ('Total energy to grid (kWh)', 'kwh_total'),
    'h-Total':  ('Total Operation hours (Hr)', 'hours_operational'),
    'Mode':     ('Operation mode', 'mode'),
    'Error':    ('Error', 'error')
}

for field in status:
    print "%-10s: %s" % field
    Gauge(status_name_map[field[0]][1], status_name_map[field[0]][0],
          registry=registry).set(field[1])

port.close()
push_to_gateway('localhost:9091', job='pv', registry=registry)
