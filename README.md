<h1 id="2b6aba2c8ec2f8b0">csv2sqlLike</h1>
<blockquote>
<p>csv2sqlLike is a package for simple data analysis using light data set(&lt;30MB). This package has filtering method similar with sql's filtering functions. Hope this package could be helpful for who analyze data in social science.</p>
</blockquote>
<p>csv2sqlLike is consistent with 2 main classes. 
<ol>
    <li>PseudoSQLFromCSV</li>
    <li>Transfer2SQLDB</li>
</ol></p>

PseudoSQLFromCSV is charging on handling data: 
<ul>
    <li>load data and heads as nested list and list from csv file</li>
    <li>filtering data under specific condition</li>
    <li>grouping data with specific head</li>
    <li>write csv file with data inside this object</li>
</ul>

Transfer2SQLDB is charging on data transferring between PseudoSQLFromCSV and DB:
<ul>
    <li>create table in DB from data inside PseudoSQLFromCSV </li>
    <li>bring data as nested list from table in DB</li>
</ul>
<h2 id="installation">Installation</h2>
<p>PIP:</p>
<pre><code class="lang-sh">pip3 <span class="hljs-keyword">install</span> <span class="hljs-keyword">csv2sqllike</span></code></pre>
<h2 id="usage-example">Usages</h2>
<h3 id="0a57d88a6757fbe1">load data from csv file</h3>

```python
data = csv2sqllike.get_data_from_csv("[path_to_file]")
# example
data = csv2sqllike.get_data_from_csv("./data.csv")
data = csv2sqllike.get_data_from_csv("./test.csv", 
                                     type_dict={'region': 'str', 'country': 'str', 'name': 'str', 'sex': 'str', 'university': 'str', 'age': 'int'}
                                    )
# check loaded data type : nested list
print(type(data.data)) 
# check data head
print(data.head)
# check first row data
print(data.data[0])
# check data
print(data.data)
```

<h3 id="244ab9819aad2312">filtering data using condition</h3>

```python
data.where("[head] [operator] [specific value]")
# example
data.where("region == east-asia")
# check conditions used
print(data.condition_where) 
# check filtered data
print(data.cache_data)
```

<h3 id="e81a2ede417bc926">grouping data using specific head</h3>

```python
data.group_by("[head]")
# example
data.group_by("region")
# check heads used for grouping data
print(data.condition_group_by)
# check grouping data stored in dictionary
print(data.cache_dict)
```

<h3 id="6ad2c7f4e3a81f92">clear cache storage(storage for filtering and grouping)</h3>

```python
# check cache stroage befor clearing caches
print(data.condition_where)
print(data.cache_data)
print(data.condition_group_by)
print(data.cache_dict)
# clear cache storage
data.clear_cache_data()
# check cache stroage after clearing caches
print(data.condition_where)
print(data.cache_data)
print(data.condition_group_by)
print(data.cache_dict)
```

<h3 id="0ac49b5eb1831fe3">add head and delete head</h3>

```python
print(data.header)
# add new head
data.add_head("new_head")
# check added head
print(data.header)
# delete head
data.delete_head("new_head")
# check heads after deleting specific head
print(data.header)
```


<p><em>For more examples and usage, please refer to the <a href="https://github.com/hoosiki/csv2sqlLike/blob/master/samples/examples.ipynb">jupyter notebook</a>.</em></p>
<h2 id="release-history">Release History</h2>
<ul>
<li>1.0.0<ul>
<li>First release</li>
</ul>
<li>1.0.1<ul>
<li>Add encoding option(default encode is utf-8)</li>
</ul>
<li>1.0.2<ul>
<li>Add auto installing for required package</li>
</ul>
<li>1.0.3<ul>
<li>Improve precision on data shape check function</li>
</ul>
</ul>
<!-- Markdown link & img dfn's -->

