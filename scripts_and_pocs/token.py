token = '857:g67?5ABBo:BtDA?tIvLDKL{MQPSRQWW.'
count = 0
result = []
for value in token:
  result.append(chr((ord(value) - count)))
  count +=1

print ("".join(result))