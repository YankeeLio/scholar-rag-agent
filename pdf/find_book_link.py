import urllib.request, re

url = 'https://udlbook.github.io/udlbook/assets/index-CMi_VvpI.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
js = urllib.request.urlopen(req, timeout=120).read().decode('utf-8', 'ignore')
print('js len:', len(js))
for m in sorted(set(re.findall(r'[^"\']*\.pdf[^"\']*', js))):
    print(m)
