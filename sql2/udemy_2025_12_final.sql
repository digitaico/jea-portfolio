SELECT *
FROM public.schools;
SELECT *
FROM public.school_details;
SELECT *
FROM public.players;

-- PART I: SCHOOL ANALYSIS

-- TASK 2: In each decade, how many schools were there that produced players? [Numeric Functions]
select ROUND(yearid, -1) decade , count(DISTINCT schoolid) as total_scools
from public.schools s
group by decade
ORDER BY decade;

-- TASK 3: What are the names of the top 5 schools that produced the most players? [Joins]
select sd.name_full, count(DISTINCT s.playerid) as total_players
from public.schools s
left join public.school_details sd 
on sd.schoolid = s.schoolid 
group by sd.name_full
ORDER BY total_players desc
limit 5;

-- TASK 4: For each decade, what were the names of the top 3 schools that produced the most players? [Window Functions]
with data as (
select ROUND(s.yearid, -1) decade , sd.name_full ,
count(DISTINCT s.playerid) as total_players
from public.schools s
left join public.school_details sd 
on sd.schoolid = s.schoolid
group by decade, sd.name_full 
),
rn as (
select d.decade , name_full, total_players, 
row_number() over (partition by decade order by total_players desc) as row_num
from data d
)
select *
from rn 
where row_num <= 3;

-- II salaries
-- TASK 1: View the salaries table
select * from salaries;

-- TASK 2: Return the top 20% of teams in terms of average annual spending [Window Functions]
with ts as (
SELECT teamid, yearid, sum(salary) as total_spend
from public.salaries s
group by teamid, yearid
order by teamid, yearid
),
sp as (
	select teamid, avg(total_spend) as avg_spend,
			NTILE(5) OVER(ORDER BY avg(total_spend) desc) as spend_pct
	from ts
	group by teamId)
select teamid, round(avg_spend/1000000, 1) as avg_spend_millions
from sp order_items 
where spend_pct = 1;

-- TASK 3: For each team, show the cumulative sum of spending over the years [Rolling Calculations]
with ts as (
select teamid, yearid, sum(salary) total_spend
from salaries
group by teamid, yearid
order by teamid, yearid
)
select teamid, yearid, 
round(sum(total_spend) over(partition by teamid order by yearid) / 1000000, 1) as cum_spend_millions
from ts;

-- TASK 4: Return the first year that each team's cumulative spending surpassed 1 billion [Min / Max Value Filtering]
with ts as (
select teamid, yearid, sum(salary) total_spend
from salaries
group by teamid, yearid
order by teamid, yearid
),
cs as (
select teamid, yearid, 
sum(total_spend) over(partition by teamid order by yearid) as cum_spend
from ts ),
billion_year as (
select *
from cs
where cum_spend > 1000000000
),
ranked_year as (
select teamid, yearid,
row_number() over(partition by teamid order by cum_spend) as year_billion
from billion_year )
select teamid, yearid
from ranked_year
where year_billion = 1;

-- PART III: PLAYER CAREER ANALYSIS

-- TASK 1: View the players table and find the number of players in the table
SELECT * FROM players;
SELECT COUNT(*) FROM players;

-- TASK 2: For each player, calculate their age at their first (debut) game, their last game,
-- and their career length (all in years). Sort from longest career to shortest career. [Datetime Functions]

select namegiven,  
--cast(birthyear || '-' || birthmonth || '-' || birthday as DATE) birthdate,
--extract(year from age(current_date, cast(birthyear || '-' || birthmonth || '-' || birthday as DATE))) as age,
--debut,
-- finalgame,
extract(year from age(debut, cast(birthyear || '-' || birthmonth || '-' || birthday as DATE))) as debut_age,
extract(year from age(finalgame, cast(birthyear || '-' || birthmonth || '-' || birthday as DATE))) as finalgame_age, 
extract(year from (age(finalgame, debut))) as career_length
from players
where debut is not null or finalgame is not null
order by career_length desc, namegiven;

-- TASK 3: What team did each player play on for their starting and ending years? [Joins]
select * from salaries;
select p.namegiven, 
s.yearid as starting_year, s.teamid as starting_team,
e.yearid as ending_year, e.teamid as ending_team 
from players p 
	inner JOIN salaries s 
		on s.playerid = p.playerid 
		and s.yearid = extract(year from p.debut)
	inner JOIN salaries e 
		on e.playerid = p.playerid 
		and e.yearid = extract(year from p.finalgame);

-- TASK 4: How many players started and ended on the same team and also played for over a decade? [Basics]
select * from salaries;
select p.namegiven, 
s.yearid as starting_year, s.teamid as starting_team,
e.yearid as ending_year, e.teamid as ending_team 
from players p 
	inner JOIN salaries s 
		on s.playerid = p.playerid 
		and s.yearid = extract(year from p.debut)
	inner JOIN salaries e 
		on e.playerid = p.playerid 
		and e.yearid = extract(year from p.finalgame)
where s.teamid = e.teamid and e.yearid - s.yearid > 10
order by p.namegiven ;


-- PART IV: PLAYER COMPARISON ANALYSIS

-- TASK 1: View the players table
SELECT * FROM players;

-- TASK 2: Which players have the same birthday? Hint: Look into GROUP_CONCAT / LISTAGG / STRING_AGG [String Functions]
with bd as (
select p.namegiven, 
cast(birthyear || '-' || birthmonth || '-' || birthday as DATE) birthdate
from players p
)
select birthdate,
string_agg(namegiven, ', ' ) as pleayers
from bd
where birthdate is not null 
and extract(year from birthdate) between 1980 and 1990
group by bd.birthdate 
having count(namegiven) > 1
order by count(namegiven) desc ;

-- TASK 3: Create a summary table that shows for each team, what percent of players bat right, left and both [Pivoting]
-- EDIT: This solution doesn't account for duplicate player rows in the salaries table. The DISTINCT solution below is the more accurate one.



