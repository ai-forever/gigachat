"""Question-answer example, using the file with the root certificate of the Russian Ministry of Digital Development for certificate verification"""

from gigachat import GigaChat

# Specify the path to the file "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer"
with GigaChat(ca_bundle_file="russian_trusted_root_ca.cer") as giga:
    response = giga.chat("What factors affect the cost of home insurance?")
    print(response.choices[0].message.content)
