-- SELECT top 10 --*
-- --c.agentNumber, c.binNumber, c.cobrand, c.mid, c.officeName, c.merchantName
-- --VALUE { MERCH_NO: c.mid }
-- c.mid
-- FROM c
-- where c.pkType = 'merchant:information' and c.pkFilter = 20251230

-- SELECT top 10 * FROM c
-- where c.pkType in ('repay:settlement', 'cybersource:authorization-') 
-- and STRINGTONUMBER(c.pkFilter) <= 20251119
-- --  and NOT CONTAINS (c.sortCodeName , c.binNumber)
-- --  and c.mid in ('911856239313','371182647325','169869415070')

SELECT c.pkFilter, COUNT(1) as cnt
FROM c
where c.pkType = 'repay:settlement' and STRINGTONUMBER(c.pkFilter) < 20251130
group by c.pkFilter
order by c.pkFilter desc

-- SELECT c.pkType,COUNT(1) as AVG_TXN_CNT
-- FROM c
-- where c.pkType = 'repay:settlement' and STRINGTONUMBER(c.pkFilter) >= 20251130
-- GROUP BY c.pkType