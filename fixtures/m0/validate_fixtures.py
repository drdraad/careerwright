"""Validate synthetic contract fixtures; this does not test a Nessa application."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def layers(points):
    remaining = dict(points)
    result = []
    while remaining:
        front = [key for key, value in remaining.items()
                 if not any(other != value and all(a <= b for a, b in zip(other, value))
                            for other in remaining.values())]
        if not front:
            raise AssertionError('Dominance relation did not produce a front')
        result.append(sorted(front))
        for key in front:
            del remaining[key]
    return result

def main():
    personas = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT/'personas').glob('*.json'))}
    assert set(personas) == {'P01', 'P02', 'P03', 'P04', 'P05'}
    assert all(p['synthetic'] and len(p['cities']) <= 3 for p in personas.values())
    trace = json.loads((ROOT/'worked_trace.json').read_text())
    assert trace['synthetic'] and trace['id'] == personas['P01']['expected']['trace_id']
    horizon = trace['comparison_horizon_months']
    baseline = sum(trace['baseline_income_by_month_minor'])
    catalogue = {a['id']: a for a in trace['catalogue']['actions']}
    assert len(catalogue) == 5
    for action in catalogue.values():
        assert action['weekly_study_envelope'] + action['weekly_work_envelope_while_active'] <= trace['available_weekly_hours_envelope']
        assert action['exclusive_group'] == 'fixture:core-training'
        assert all(o['review_state'] == 'accepted_assumption' for o in action['outcomes'])
    points = {}
    for route in trace['routes']:
        action = catalogue[route['action_ids'][0]]
        assert action['fees_by_month_minor'] == route['payments_by_month_minor']
        assert action['scenario_net_income_by_month_minor'] == route['income_by_month_minor']
        assert len(action['intakes'][0]['active_months']) == route['time_months']
        assert len(route['income_by_month_minor']) == len(route['payments_by_month_minor']) == horizon
        assert sum(route['payments_by_month_minor']) == route['direct_spend_minor']
        economic = route['direct_spend_minor'] + baseline - sum(route['income_by_month_minor'])
        assert economic == route['economic_cost_minor']
        assert route['direct_spend_minor'] <= personas['P01']['direct_spend_cap_minor']
        assert max(route['payments_by_month_minor']) <= personas['P01']['monthly_payment_cap_minor']
        points[route['id']] = (route['time_months'], economic)
        cash = trace['opening_cash_minor']
        lower_bounds = []
        for income, payment, living in zip(route['income_by_month_minor'], route['payments_by_month_minor'], trace['living_outgoings_by_month_minor']):
            prefunded = cash - payment - living
            assert prefunded >= trace['minimum_reserve_minor']
            lower_bounds.append(prefunded)
            cash = prefunded + income  # All fixture wages arrive later in the month.
        if route['id'] == trace['expected']['selected_route']:
            printed = trace['expected']['print_snapshot']
            assert route['time_months'] == printed['time_months']
            assert economic == printed['economic_cost_minor']
            assert route['direct_spend_minor'] == printed['direct_spend_minor']
            assert max(route['payments_by_month_minor']) == printed['peak_monthly_payment_minor']
            assert min(lower_bounds) == printed['minimum_prefunded_cash_minor']
    assert layers(points) == trace['expected']['fronts']
    assert layers({'a': (1, 3), 'b': (2, 2), 'c': (3, 1), 'q': (4, 4)}) == [['a', 'b', 'c'], ['q']]
    assert layers({'a': (1, 1), 'b': (1, 1)}) == [['a', 'b']]
    assert layers(dict(zip('ABCDEFGHI', [(6,4800),(9,2400),(12,900),(8,5400),(11,3000),(14,1200),(10,6200),(13,3600),(16,1600)]))) == [list('ABC'),list('DEF'),list('GHI')]
    assert 100 + 300 - 200 >= 0 and 100 - 200 < 0  # Month-end balance can conceal an early overdraft.
    assert 20 + 20 <= 4 * 20 and 20 + 20 > 20  # A monthly total can conceal one overloaded week.
    assert 3000 + 12*2000 - 6*2000 == 15000  # FIN-1 common-horizon example.
    for outcome in trace['course_outcomes']:
        span = outcome['source_span']
        assert 0 <= span['start'] < span['end'] <= len(trace['syllabus_text'])
        assert span['source_hash'] == hashlib.sha256(trace['syllabus_text'].encode()).hexdigest()
        assert outcome['claim_state'] == 'planned_conditional'
    score = trace['expected']['score_record']
    assert (score['range'][0] >= score['minimum_filter']) == score['lower_bound_filter_passes']
    assert personas['P03']['expected']['reject_option']['upfront_fee_minor'] > personas['P03']['monthly_payment_cap_minor']
    assert personas['P04']['regulatory_gate']['kind'] == 'statutory'
    assert personas['P04']['expected']['reject_gate_demotion']
    assert all(s['evidenced'] >= s['required'] for s in personas['P05']['skills'])
    corpus = json.loads((ROOT/'source_corpus_manifest.json').read_text())
    assert corpus['status'] == 'required_corpus_not_collected'
    print(json.dumps({'status': 'passed', 'personas': 5, 'trace': 'TRACE-01',
                      'scope': 'fixture arithmetic, shape and stated invariants only',
                      'application_end_to_end_tested': False, 'real_source_corpus_collected': False}, indent=2))

if __name__ == '__main__':
    main()
