<html>
<head>
    <title>Itest Test Report</title>
    <style>
body {
    font-family: 'Courier New',Courier,Freemono,'Nimbus Mono L',monospace,Arial,Helmet,Freesans,sans-serif;;
}
table {
    border-collapse:collapse;
    text-align: center;
}
th { background-color: #F3F3F3 }
td, th {
    border: 1px solid grey;
    padding: 3px
}
td {
    font-size: 1.3em;
}
.bad {
    background-color: #FF1111;
}
.warn {
    background-color: yellow;
}
.bigger {
    font-size: 1.3em;
    color: limegreen;
}
.pre {
    margin-bottom: 2em;
}
    </style>
    <script type='text/javascript' src='http://code.jquery.com/jquery-1.8.3.min.js'></script>
    <script type='text/javascript'>
$(document).ready(function() {
    $('td.na').html('N/A');
    $('td.na1').html('running');
});
    </script>
</head>
<body>


<div style='width:98%; position: absolute'>
    <div style='float:right'>
        <a href='/report/list'>All reports</a>
        &nbsp;&nbsp;
        <a href='/report'>Latest report</a>
    </div>
</div>


<div style='margin-left:1em'>
<h1>Itest Test Report</h1>
<ul class='pre'>
    %if version:
    <li>{{version}}</li>
    %end
    <li>{{start_date}}</li>
    <li>Run <span class='bigger'>{{total_cases}}</span> functional cases in total,
        which cost <span class='bigger'>{{mean_cost}}</span> for average</li>
</ul>

<table>
    <tr>
        <th>Arch/Dist</th>
        %for col_name in col_names:
        <th>{{col_name}}</th>
        %end
    </tr>

    %for i, row_name in enumerate(row_names):
    <tr>
        <th>{{row_name}}</th>

        %for txt, href in table[i]:
            %if href is None:
        <td>{{txt}}</td>
            %else:
        <td><a href={{href}}>{{txt}}</a></td>
            %end
<!--        <td><a href='OpenSUSE12.1/x86/release/logs/report.html'>3/267</a></td> -->
        %end
    </tr>
    %end
</table>
</div>
<div>

<!--
<h3>Full build result</h3>
    <p><a>RSA-Packages-Build-Report-xxx.xlsx</a></p>
</div>
-->

</body>
</html>
