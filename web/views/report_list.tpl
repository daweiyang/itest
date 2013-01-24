<html>
<head>
    <title>Report List</title>
</head>
<body>

%if names:
    <h1>All reports available, in descendent order by mtime</h1>

    <ul>
    %for name in names:
        <li><a href="/report/{{name}}">{{name}}</a></li>
    %end
    </ul>
%else:
    <h1>No reports available</h1>
%end
</body>
</html>