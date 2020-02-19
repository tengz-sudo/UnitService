from gurobipy import *
import pandas as pd
import numpy as np

def unconstrained_qp(services_to_consider, units_to_consider, service_count_daily_dicts,
                    unit_cap_dict, cap_thresh = 0.9):
    # Input:
    # services_to_consider: list of services
    # units_to_consider: list of units
    # service_count_daily_dicts: list of dict; each element is a service:count dict in a day
    # unit_cap_dict: dict; unit:capacity
    # cap_thresh: what fraction of capacity should we target on

    model = Model()

    variables = model.addVars(services_to_consider, units_to_consider, vtype = GRB.BINARY)

    # # constraint-2: hemonc and stem cell should not be moved
    # model.addConstr(variables[('Hematology/Oncology', 'HOPCU')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Stem Cell Transplant', 'SCTPCU')], GRB.EQUAL, 1)

    # constraints-1: for each service, only one should be 1
    for service in services_to_consider:
        expr = LinExpr()
        for unit in units_to_consider:
            expr += variables[(service, unit)]
        model.addConstr(expr, GRB.EQUAL, 1)

    # objective quadratic, sum_{day, unit} of (unit_cap - daily_unit_occupacy)^2
    obj = QuadExpr()
    for day_counts in service_count_daily_dicts:
        for unit in units_to_consider:
            diff = LinExpr()
            for service in services_to_consider:
                diff += variables[(service, unit)]*day_counts[service]
            diff -= unit_cap_dict[unit] * cap_thresh
            obj += diff*diff
    model.setObjective(obj)

    # Solve
    model.optimize()

    # Write model to a file
    model.write('qp.lp')

    # create allocation
    allocation = pd.DataFrame()
    allocation['Service'] = services_to_consider
    for unit in units_to_consider:
        allocation[unit] = 0
    allocation = allocation.set_index('Service')

    if model.status == GRB.Status.OPTIMAL:
        sol = model.getAttr('x', variables)
        for service in services_to_consider:
            for unit in units_to_consider:
                if sol[(service, unit)] == 1:
                    allocation.loc[service, unit] = 1
    return allocation



def constrained_qp(services_to_consider, units_to_consider, service_count_daily,
                    unit_cap_dict, cap_thresh = 0.9):
    # Input:
    # services_to_consider: list of services
    # units_to_consider: list of units
    # service_count_daily_dicts: list of dict; each element is a service:count dict in a day
    # unit_cap_dict: dict; unit:capacity
    # cap_thresh: what fraction of capacity should we target on

    model = Model()

    # create a dictionary for optimazation
    service_count_daily_dicts = [{service:row[service] for service in services_to_consider }
                             for index, row in service_count_daily.iterrows()]

    variables = model.addVars(services_to_consider, units_to_consider, vtype = GRB.BINARY)

    # constraint-0: services can not be moved
    model.addConstr(variables[('Green Team', 'PCU300')], GRB.EQUAL, 1)
    model.addConstr(variables[('Red Team', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Liver Transplant', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Kidney Transplant', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Transplant Surgery', 'PCU300')], GRB.EQUAL, 1)
    # Transplants in 500
    # model.addConstr(variables[('Green Team', 'PCU500')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Red Team', 'PCU500')], GRB.EQUAL, 1)

    model.addConstr(variables[('Neurology', 'PCU400')], GRB.EQUAL, 1)
    model.addConstr(variables[('Neurosurgery', 'PCU400')], GRB.EQUAL, 1)
    model.addConstr(variables[('Pulmonary', 'PCU400')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Yellow Team', 'PCU400')], GRB.EQUAL, 1)

    model.addConstr(variables[('HemeOnc and StemCell', 'PCU500')], GRB.EQUAL, 1)

    model.addConstr(variables[('Cardiology', 'PCU200')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Cardiovascular Transplant', 'PCU200')], GRB.EQUAL, 1)

    # model.addConstr(variables[('Cardiovascular Transplant', 'PCU200')], GRB.EQUAL, 1)

    model.addConstr(variables[('Otolaryngology (ENT)', 'PCU360')], GRB.EQUAL, 0)
    if "General Pediatrics 1" in services_to_consider:
        model.addConstr(variables[('General Pediatrics 1', 'PCU500')], GRB.EQUAL, 0)
        model.addConstr(variables[('General Pediatrics 2', 'PCU500')], GRB.EQUAL, 0)
    # under 90%, 300/400, 200, 500

    # PCU 200 only Cardiology
    model.addConstr(1 == quicksum(
                        [variables[(se, 'PCU200')] for se in services_to_consider ]
                        )
                    )

    # constraints-1: for each service, only one should be 1
    for service in services_to_consider:
        expr = LinExpr()
        for unit in units_to_consider:
            expr += variables[(service, unit)]
        model.addConstr(expr, GRB.EQUAL, 1)

    # objective quadratic, sum_{day, unit} of (unit_cap - daily_unit_occupacy)^2
    obj = QuadExpr()
    for day_counts in service_count_daily_dicts:
        for unit in units_to_consider:
            diff = LinExpr()
            for service in services_to_consider:
                diff += variables[(service, unit)]*day_counts[service]
            diff -= unit_cap_dict[unit] * cap_thresh
            obj += diff*diff
    model.setObjective(obj)

    # Solve
    model.optimize()

    # Write model to a file
    model.write('qp.lp')

    # create allocation
    allocation = pd.DataFrame()
    allocation['Service'] = services_to_consider
    for unit in units_to_consider:
        allocation[unit] = 0
    allocation = allocation.set_index('Service')

    if model.status == GRB.Status.OPTIMAL:
        sol = model.getAttr('x', variables)
        for service in services_to_consider:
            for unit in units_to_consider:
                if sol[(service, unit)] == 1:
                    allocation.loc[service, unit] = 1
    return allocation




def constrained_piecewise(services_to_consider, units_to_consider, service_count_daily,
                    unit_cap_dict, cap_thresh = 0.95, ptu = [-1, -0.01, 0.01, 1], ptf = [0, 0, 1, 1]):
    # Input:
    # services_to_consider: list of services
    # units_to_consider: list of units
    # service_count_daily_dicts: list of dict; each element is a service:count dict in a day
    # unit_cap_dict: dict; unit:capacity
    # cap_thresh: what fraction of capacity should we target on
    model = Model()

    variables = model.addVars(services_to_consider, units_to_consider, vtype = GRB.BINARY)

    # create a dictionary for optimazation
    service_count_daily_dicts = [{service:row[service] for service in services_to_consider }
                             for index, row in service_count_daily.iterrows()]

    day_unit_sum_vars = model.addVars(np.arange(len(service_count_daily_dicts)),
                                      units_to_consider, vtype = GRB.CONTINUOUS)

    variables = model.addVars(services_to_consider, units_to_consider, vtype = GRB.BINARY)

    # constraint-0: services can not be moved
    model.addConstr(variables[('Green Team', 'PCU300')], GRB.EQUAL, 1)
    model.addConstr(variables[('Red Team', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Liver Transplant', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Kidney Transplant', 'PCU300')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Transplant Surgery', 'PCU300')], GRB.EQUAL, 1)
    # Transplants in 500
    # model.addConstr(variables[('Green Team', 'PCU500')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Red Team', 'PCU500')], GRB.EQUAL, 1)

    model.addConstr(variables[('Neurology', 'PCU400')], GRB.EQUAL, 1)
    model.addConstr(variables[('Neurosurgery', 'PCU400')], GRB.EQUAL, 1)
    model.addConstr(variables[('Pulmonary', 'PCU400')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Yellow Team', 'PCU400')], GRB.EQUAL, 1)

    model.addConstr(variables[('HemeOnc and StemCell', 'PCU500')], GRB.EQUAL, 1)

    model.addConstr(variables[('Cardiology', 'PCU200')], GRB.EQUAL, 1)
    # model.addConstr(variables[('Cardiovascular Transplant', 'PCU200')], GRB.EQUAL, 1)

    model.addConstr(variables[('Otolaryngology (ENT)', 'PCU360')], GRB.EQUAL, 0)
    if "General Pediatrics 1" in services_to_consider:
        model.addConstr(variables[('General Pediatrics 1', 'PCU500')], GRB.EQUAL, 0)
        model.addConstr(variables[('General Pediatrics 2', 'PCU500')], GRB.EQUAL, 0)
    # under 90%, 300/400, 200, 500

    # PCU 200 only Cardiology
    model.addConstr(1 == quicksum(
                        [variables[(se, 'PCU200')] for se in services_to_consider ]
                        )
                    )

    # constraints-1: for each service, only one should be 1
    for service in services_to_consider:
        expr = LinExpr()
        for unit in units_to_consider:
            expr += variables[(service, unit)]
        model.addConstr(expr, GRB.EQUAL, 1)

    # set piecewise linear objective
    for ind, day_counts in enumerate(service_count_daily_dicts):
        for unit in units_to_consider:
            census_sum = LinExpr()
            for service in services_to_consider:
                census_sum += variables[(service, unit)]*day_counts[service]
            census_sum -= unit_cap_dict[unit] * cap_thresh
            model.addConstr(census_sum - day_unit_sum_vars[(ind, unit)], GRB.LESS_EQUAL, 0)
            model.setPWLObj(day_unit_sum_vars[(ind, unit)], ptu, ptf)

    # Solve
    model.optimize()

    # Write model to a file
    model.write('piecewise.lp')

    # create allocation
    allocation = pd.DataFrame()
    allocation['Service'] = services_to_consider
    for unit in units_to_consider:
        allocation[unit] = 0
    allocation = allocation.set_index('Service')

    if model.status == GRB.Status.OPTIMAL:
        sol = model.getAttr('x', variables)
        for service in services_to_consider:
            for unit in units_to_consider:
                if sol[(service, unit)] == 1:
                    allocation.loc[service, unit] = 1
    return allocation


# dd
