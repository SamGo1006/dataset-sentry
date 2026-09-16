"""Audit CSV data against an explicit schema. Python standard library only."""
import argparse
import csv
import json
import math
import sys
from datetime import date

def validate_schema(schema):
    if not isinstance(schema, dict) or not schema:
        raise ValueError('schema must be a nonempty object of column rules')
    for name, rule in schema.items():
        if not isinstance(name, str) or not name or not isinstance(rule, dict):
            raise ValueError('each column needs a name and rule object')
        if set(rule) - {'type', 'required', 'unique', 'min', 'max', 'enum'}:
            raise ValueError(f'unknown rule for {name}')
        if rule.get('type', 'string') not in {'string', 'integer', 'number', 'date'}:
            raise ValueError(f'unsupported type for {name}')
        for flag in ('required', 'unique'):
            if flag in rule and type(rule[flag]) is not bool:
                raise ValueError(f'{flag} must be boolean')
        for bound in ('min', 'max'):
            if bound in rule and (rule.get('type') not in {'integer', 'number'} or
                type(rule[bound]) not in (int, float) or not math.isfinite(rule[bound])):
                raise ValueError('bounds require finite numbers and a numeric type')
        if 'min' in rule and 'max' in rule and rule['min'] > rule['max']:
            raise ValueError('min cannot exceed max')
        if 'enum' in rule and (not isinstance(rule['enum'], list) or
                              not all(isinstance(v, str) for v in rule['enum'])):
            raise ValueError('enum must be a list of raw string values')

def audit(stream, schema, max_issues=100):
    validate_schema(schema)
    if type(max_issues) is not int or max_issues < 0:
        raise ValueError('max_issues must be a nonnegative integer')
    reader = csv.DictReader(stream, strict=True)
    headers = reader.fieldnames or []
    if not headers or len(set(headers)) != len(headers):
        raise ValueError('CSV needs nonempty, unique headers')
    if any(not name for name in headers):
        raise ValueError('column names cannot be empty')
    missing = sorted(set(schema) - set(headers))
    if missing:
        raise ValueError('missing columns: ' + ', '.join(missing))
    issues, total, rows = [], 0, 0
    seen = {name: set() for name, rule in schema.items() if rule.get('unique')}
    def issue(row, column, code):
        nonlocal total
        total += 1
        if len(issues) < max_issues:
            issues.append({'row': row, 'column': column, 'code': code})
    for row_number, row in enumerate(reader, 2):
        rows += 1
        if None in row or any(v is None for v in row.values()):
            issue(row_number, '*', 'column_count')
        for name, rule in schema.items():
            raw = row.get(name)
            if raw is None or raw.strip() == '':
                if rule.get('required'):
                    issue(row_number, name, 'required')
                continue
            try:
                kind = rule.get('type', 'string')
                value = {'integer': int, 'number': float, 'date': date.fromisoformat,
                         'string': str}[kind](raw)
                if kind == 'number' and not math.isfinite(value):
                    raise ValueError('nonfinite')
            except (ValueError, OverflowError):
                issue(row_number, name, 'type')
                continue
            if 'min' in rule and value < rule['min']:
                issue(row_number, name, 'min')
            if 'max' in rule and value > rule['max']:
                issue(row_number, name, 'max')
            if 'enum' in rule and raw not in rule['enum']:
                issue(row_number, name, 'enum')
            if name in seen:
                if value in seen[name]:
                    issue(row_number, name, 'duplicate')
                seen[name].add(value)
    return {'rows': rows, 'issue_count': total, 'issues': issues,
            'truncated': total > len(issues), 'valid': total == 0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file')
    parser.add_argument('schema_file')
    parser.add_argument('--max-issues', type=int, default=100)
    args = parser.parse_args()
    try:
        with open(args.schema_file, encoding='utf-8') as f:
            schema = json.load(f)
        with open(args.csv_file, encoding='utf-8-sig', newline='') as f:
            result = audit(f, schema, args.max_issues)
        print(json.dumps(result, indent=2))
        return 0 if result['valid'] else 1
    except (OSError, ValueError, csv.Error) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
