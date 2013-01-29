#!/usr/bin/env python
# This script generate a shit ton of random alerts
# It can be used to build a testing/dev environment

elements = "Hydrogen,Helium,Lithium,Beryllium,Boron,Carbon,Nitrogen,Oxygen,Fluorine,Neon,Sodium,Magnesium,Aluminium,Silicon,Phosphorus,Sulfur,Chlorine,Argon,Potassium,Calcium,Scandium,Titanium,Vanadium,Chromium,Manganese,Iron,Cobalt,Nickel,Copper,Zinc,Gallium,Germanium,Arsenic,Selenium,Bromine,Krypton,Rubidium,Strontium,Yttrium,Zirconium,Niobium,Molybdenum,Technetium,Ruthenium,Rhodium,Palladium,Silver,Cadmium,Indium,Tin,Antimony,Tellurium,Iodine,Xenon,Caesium,Barium,Lanthanum,Cerium,Praseodymium,Neodymium,Promethium,Samarium,Europium,Gadolinium,Terbium,Dysprosium,Holmium,Erbium,Thulium,Ytterbium,Lutetium,Hafnium,Tantalum,Tungsten,Rhenium,Osmium,Iridium,Platinum,Gold,Mercury,Thallium,Lead,Bismuth,Polonium,Astatine,Radon,Francium,Radium,Actinium,Thorium,Protactinium,Uranium,Neptunium,Plutonium,Americium,Curium,Berkelium,Californium,Einsteinium,Fermium,Mendelevium,Nobelium,Lawrencium,Rutherfordium,Dubnium,Seaborgium,Bohrium,Hassium,Meitnerium,Darmstadtium,Roentgenium,Copernicium,Ununtrium,Flerovium,Ununpentium,Livermorium,Ununseptium,Ununoctium".split(',')

airports = "BOS,SFO,JFK,LAX".split(',')

environments = "Production,QA".split(',')

lorem = '''Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

# give OK (0) a slightly higher chance
statuses = "0,0,0,0,0,0,0,0,0,1,1,1,2,2,2,2,3".split(',')

states = "Alabama,Alaska,Arizona Arkansas,California,Colorado,Connecticut,Delaware,Florida,Georgia, Hawaii,Idaho,Illinois, Indiana, Iowa, Kansas,Kentucky, Louisiana,Maine,Maryland,Massachusetts,Michigan, Minnesota,Mississippi,Missouri, Montana, Nebraska, Nevada,New Hampshire,New Jersey,New Mexico,New York,North Carolina,North Dakota, Ohio, Oklahoma,Oregon,Pennsylvania, Rhode Island, South Carolina,South Dakota, Tennessee,Texas,Utah,Vermont Virginia, Washington,West Virginia,Wisconsin,Wyoming".split(',')

countries = "Afghanistan,Albania ,Algeria ,American,Andorra ,Angola,Anguilla,Antigua,Argentina,Armenia ,Aruba,ia,Austria ,Azerbaijan,Bahamas ,Bahrain ,Bangladesh,Barbados,Belarus ,Belgium ,Belize,Benin,Bermuda ,Bhutan,Bolivia ,Bosnia-Herzegovina,Botswana,Bouvet Island,Brazil,Brunei,Bulgaria,Burkina Faso,Burundi ,Cambodia,Cameroon,Canada,Cape Verde,Cayman Islands,Chad,Chile,China,Christmas Island,Cocos (Keeling) Islands ,Colombia,Comoros ,Congo,Cook Islands,Costa Rica,Croatia ,Cuba,Cyprus,Czech Republic,Denmark ,Djibouti,Dominica,Dominican Republic,Ecuador ,Egypt,El Salvador ,Equatorial Guinea,Eritrea ,Estonia ,Ethiopia,Falkland Islands,Faroe Islands,Fiji,Finland ,France,French Guiana,Gabon,Gambia,Georgia ,Germany ,Ghana,Gibraltar,Greece,Greenland,Grenada ,Guadeloupe,Guam,Guatemala,Guinea,Guinea Bissau,Guyana,Haiti,Holy See,Honduras,Hong Kong,Hungary ,Iceland ,India,Indonesia,Iran,Iraq,Ireland ,Israel,Italy,Ivory Coast ,Jamaica ,Japan,Jordan,Kazakhstan,Kenya,Kiribati,Kuwait,Kyrgyzstan,Laos,Latvia,Lebanon ,Lesotho ,Liberia ,Libya,Liechtenstein,Lithuania,Luxembourg,Macau,Macedonia,Madagascar,Malawi,Malaysia,Maldives,Mali,Malta,Marshall Islands,Martinique,Mauritania,Mauritius,Mayotte ,Mexico,Micronesia,Moldova ,Monaco,Mongolia,Montenegro,Montserrat,Morocco ,Mozambique,Myanmar ,Namibia ,Nauru,Nepal,Netherlands ,Netherlands Antilles,New Caledonia,New Zealand ,Nicaragua,Niger,Nigeria ,Niue,Norfolk Island,North Korea ,Northern Mariana Islands,Norway,Oman,Pakistan,Palau,Panama,Papua New Guinea,Paraguay,Peru,Philippines ,Pitcairn Island ,Poland,Polynesia,Portugal,Puerto Rico ,Qatar,Reunion ,Romania ,Russia,Rwanda,San Marino,Saudi Arabia,Senegal ,Serbia,Seychelles,Sierra Leone,Singapore,Slovakia,Slovenia,Solomon Islands ,Somalia ,South,South Georgia,South Korea ,Spain,Sri Lanka,Sudan,Suriname,Svalbard,Swaziland,Sweden,Switzerland ,Syria,Taiwan,Tajikistan,Tanzania,Thailand,Timor-Leste ,Togo,Tokelau ,Tonga,Trinidad,Tunisia ,Turkey,Turkmenistan,Turks and Caicos Islands,Tuvalu,Uganda,Ukraine ,United Arab Emirates,United Kingdom,United States,Uruguay ,Uzbekistan,Vanuatu ,Venezuela,Vietnam ,Virgin Islands,Wallis and Futuna Islands,Yemen,Zambia,Zimbabwe".split(',')

import os
from random import choice
from random import sample
from random import randint
from time import sleep

foobar = False
while foobar == False:
    for i in range(0,randint(0,100)):
        environment = choice(environments).strip()
        colo = choice(airports).strip()
        host = choice(elements).strip()
        service = choice(states).strip()
        status = choice(statuses).strip()
        tag = sample(countries,randint(1,9))
        tag.append('silent')
        tag = ",".join(tag)
        print environment,colo,host,service,status,tag
        os.system('python ../raven/raven -e "%s" -C "%s" -H "%s" -v "%s" -s "%s" -T "%s" -m "%s" -c ../raven/raven.conf' % (environment, colo, host, service, status, tag, lorem))
    sleep(60)  
