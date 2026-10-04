SELECT d.department_name, AVG(j.max_salary) AS average_max_salary
FROM departments AS d
JOIN employees AS e ON e.department_id = d.department_id
JOIN jobs AS j ON j.job_id = e.job_id
GROUP BY d.department_id, d.department_name
HAVING AVG(j.max_salary) > 8000;
