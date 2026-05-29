# Database Final

[<img height="630" alt="erd" src="https://github.com/user-attachments/assets/8adae5ea-d550-46b1-92ef-43777adf54d0" />](https://app.diagrams.net/#Uhttps%3A%2F%2Fgithub.com%2Fmalingsuo%2Fdatabase-final%2Freleases%2Fdownload%2Fresource%2Ferd.drawio)
<details>
<summary>ER to DB</summary>

<p>

<strong>Step 1:</strong> 將所有一般Entity types轉換為Table<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>)<br>
    student(<ins>student_id</ins>, name, admission_year)<br>
    token(<ins>id</ins>, token)<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>id</ins>, course_code, year, semester, name, credits, type, label, is_core)<br>
</p>
<p>
<strong>Step 4:</strong> 處理1:1 Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, <span style="color:red">department_id (FK), user_id (FK)</span>)<br>
    student(<ins>student_id</ins>, name, admission_year, <span style="color:red">user_id (FK)</span>)<br>
    token(<ins>id</ins>, token)<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>id</ins>, course_code, year, semester, name, credits, type, label, is_core)<br>
</p>
<p>
<strong>Step 5:</strong> 處理1:N Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, department_id (FK), user_id (FK))<br>
    student(<ins>student_id</ins>, name, admission_year, user_id (FK))<br>
    token(<ins>id</ins>, token, <span style="color:red">account_id (FK)</span>)<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>id</ins>, course_code, year, semester, name, credits, type, label, is_core, <span style="color:red">department_id (FK)</span>)<br>
</p>
<p>
<strong>Step 6:</strong> 處理M:N Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, department_id (FK), user_id (FK))<br>
    student(<ins>student_id</ins>, name, admission_year, user_id (FK))<br>
    token(<ins>id</ins>, token, account_id (FK))<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>id</ins>, course_code, year, semester, name, credits, type, label, is_core, department_id (FK))<br>
    <span style="color:red">enrollment(<ins>student_id</ins>, <ins>course_id</ins>, year, semester, grade, is_passed)</span><br>
    <span style="color:red">fields_of_study(<ins>student_id</ins>, <ins>department_id</ins>, program_type, enrollment_year)</span><br>
</details>

### DB Schema
account(<ins>id</ins>, email, password, role) \
administrator(<ins>id</ins>, department_id (FK), user_id (FK)) \
student(<ins>student_id</ins>, name, admission_year, user_id (FK)) \
token(<ins>id</ins>, token, account_id (FK)) \
department(<ins>id</ins>, college, name) \
course(<ins>id</ins>, course_code, year, semester, name, credits, type, label, is_core, department_id (FK)) \
enrollment(<ins>student_id</ins>, <ins>course_id</ins>, year, semester, grade, is_passed) \
fields_of_study(<ins>student_id</ins>, <ins>department_id</ins>, program_type, enrollment_year)
