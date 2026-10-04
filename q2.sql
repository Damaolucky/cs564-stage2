SELECT d.department_name, COUNT(e.employee_id) AS employee_count
FROM departments AS d
LEFT JOIN employees AS e ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY employee_count DESC, d.department_name ASC;
