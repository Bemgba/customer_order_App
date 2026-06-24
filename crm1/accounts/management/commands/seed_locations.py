"""
Management command: seed_locations
Populates accounts_country, accounts_state, accounts_lga with Nigerian data.

Safe to run multiple times — uses get_or_create so no duplicates.
Called automatically from build.sh on every Render deploy.

Usage:
    python manage.py seed_locations
"""
from django.core.management.base import BaseCommand
from django.db import transaction


# ---------------------------------------------------------------------------
# Data — Nigeria: 36 states + FCT, with all LGAs
# Format:  (state_id, state_name, [lga_name, ...])
# state_id follows ISO 3166-2:NG codes (NG-XX)
# ---------------------------------------------------------------------------
NIGERIA_STATES = [
    ("NG-AB", "Abia", [
        "Aba North", "Aba South", "Arochukwu", "Bende", "Ikwuano",
        "Isiala Ngwa North", "Isiala Ngwa South", "Isuikwuato", "Obi Ngwa",
        "Ohafia", "Osisioma", "Ugwunagbo", "Ukwa East", "Ukwa West",
        "Umuahia North", "Umuahia South", "Umu Nneochi",
    ]),
    ("NG-AD", "Adamawa", [
        "Demsa", "Fufure", "Ganye", "Gayuk", "Gombi", "Grie", "Hong",
        "Jada", "Lamurde", "Madagali", "Maiha", "Mayo Belwa", "Michika",
        "Mubi North", "Mubi South", "Numan", "Shelleng", "Song", "Toungo",
        "Yola North", "Yola South",
    ]),
    ("NG-AK", "Akwa Ibom", [
        "Abak", "Eastern Obolo", "Eket", "Esit Eket", "Essien Udim",
        "Etim Ekpo", "Etinan", "Ibeno", "Ibesikpo Asutan", "Ibiono-Ibom",
        "Ika", "Ikono", "Ikot Abasi", "Ikot Ekpene", "Ini", "Itu",
        "Mbo", "Mkpat-Enin", "Nsit-Atai", "Nsit-Ibom", "Nsit-Ubium",
        "Obot Akara", "Okobo", "Onna", "Oron", "Oruk Anam", "Udung-Uko",
        "Ukanafun", "Uruan", "Urue-Offong/Oruko", "Uyo",
    ]),
    ("NG-AN", "Anambra", [
        "Aguata", "Anambra East", "Anambra West", "Anaocha", "Awka North",
        "Awka South", "Ayamelum", "Dunukofia", "Ekwusigo", "Idemili North",
        "Idemili South", "Ihiala", "Njikoka", "Nnewi North", "Nnewi South",
        "Ogbaru", "Onitsha North", "Onitsha South", "Orumba North",
        "Orumba South", "Oyi",
    ]),
    ("NG-BA", "Bauchi", [
        "Alkaleri", "Bauchi", "Bogoro", "Damban", "Darazo", "Dass",
        "Gamawa", "Ganjuwa", "Giade", "Itas/Gadau", "Jama'are", "Katagum",
        "Kirfi", "Misau", "Ningi", "Shira", "Tafawa Balewa", "Toro",
        "Warji", "Zaki",
    ]),
    ("NG-BE", "Benue", [
        "Ado", "Agatu", "Apa", "Buruku", "Gboko", "Guma", "Gwer East",
        "Gwer West", "Katsina-Ala", "Konshisha", "Kwande", "Logo",
        "Makurdi", "Obi", "Ogbadibo", "Ohimini", "Oju", "Okpokwu",
        "Otukpo", "Tarka", "Ukum", "Ushongo", "Vandeikya",
    ]),
    ("NG-BO", "Borno", [
        "Abadam", "Askira/Uba", "Bama", "Bayo", "Biu", "Chibok",
        "Damboa", "Dikwa", "Gubio", "Guzamala", "Gwoza", "Hawul",
        "Jere", "Kaga", "Kala/Balge", "Konduga", "Kukawa", "Kwaya Kusar",
        "Mafa", "Magumeri", "Maiduguri", "Marte", "Mobbar", "Monguno",
        "Ngala", "Nganzai", "Shani",
    ]),
    ("NG-CR", "Cross River", [
        "Abi", "Akamkpa", "Akpabuyo", "Bakassi", "Bekwarra", "Biase",
        "Boki", "Calabar Municipal", "Calabar South", "Etung", "Ikom",
        "Obanliku", "Obubra", "Obudu", "Odukpani", "Ogoja", "Yakuur", "Yala",
    ]),
    ("NG-DE", "Delta", [
        "Aniocha North", "Aniocha South", "Bomadi", "Burutu", "Ethiope East",
        "Ethiope West", "Ika North East", "Ika South", "Isoko North",
        "Isoko South", "Ndokwa East", "Ndokwa West", "Okpe", "Oshimili North",
        "Oshimili South", "Patani", "Sapele", "Udu", "Ughelli North",
        "Ughelli South", "Ukwuani", "Uvwie", "Warri North", "Warri South",
        "Warri South West",
    ]),
    ("NG-EB", "Ebonyi", [
        "Abakaliki", "Afikpo North", "Afikpo South", "Ebonyi", "Ezza North",
        "Ezza South", "Ikwo", "Ishielu", "Ivo", "Izzi", "Ohaozara",
        "Ohaukwu", "Onicha",
    ]),
    ("NG-ED", "Edo", [
        "Akoko-Edo", "Egor", "Esan Central", "Esan North East", "Esan South East",
        "Esan West", "Etsako Central", "Etsako East", "Etsako West",
        "Igueben", "Ikpoba Okha", "Orhionmwon", "Oredo", "Ovia North East",
        "Ovia South West", "Owan East", "Owan West", "Uhunmwonde",
    ]),
    ("NG-EK", "Ekiti", [
        "Ado Ekiti", "Efon", "Ekiti East", "Ekiti South West", "Ekiti West",
        "Emure", "Gbonyin", "Ido Osi", "Ijero", "Ikere", "Ikole", "Ilejemeje",
        "Irepodun/Ifelodun", "Ise/Orun", "Moba", "Oye",
    ]),
    ("NG-EN", "Enugu", [
        "Aninri", "Awgu", "Enugu East", "Enugu North", "Enugu South",
        "Ezeagu", "Igbo Etiti", "Igbo Eze North", "Igbo Eze South", "Isi Uzo",
        "Nkanu East", "Nkanu West", "Nsukka", "Oji River", "Udenu",
        "Udi", "Uzo Uwani",
    ]),
    ("NG-FC", "FCT - Abuja", [
        "Abaji", "Bwari", "Gwagwalada", "Kuje", "Kwali", "Municipal Area Council",
    ]),
    ("NG-GO", "Gombe", [
        "Akko", "Balanga", "Billiri", "Dukku", "Funakaye", "Gombe",
        "Kaltungo", "Kwami", "Nafada", "Shomgom", "Yamaltu/Deba",
    ]),
    ("NG-IM", "Imo", [
        "Aboh Mbaise", "Ahiazu Mbaise", "Ehime Mbano", "Ezinihitte",
        "Ideato North", "Ideato South", "Ihitte/Uboma", "Ikeduru",
        "Isiala Mbano", "Isu", "Mbaitoli", "Ngor Okpala", "Njaba",
        "Nkwerre", "Nwangele", "Obowo", "Oguta", "Ohaji/Egbema",
        "Okigwe", "Onuimo", "Orlu", "Orsu", "Oru East", "Oru West",
        "Owerri Municipal", "Owerri North", "Owerri West",
    ]),
    ("NG-JI", "Jigawa", [
        "Auyo", "Babura", "Biriniwa", "Birnin Kudu", "Buji", "Dutse",
        "Gagarawa", "Garki", "Gumel", "Guri", "Gwaram", "Gwiwa", "Hadejia",
        "Jahun", "Kafin Hausa", "Kaugama", "Kazaure", "Kiri Kasama",
        "Kiyawa", "Maigatari", "Malam Madori", "Miga", "Ringim", "Roni",
        "Sule Tankarkar", "Taura", "Yankwashi",
    ]),
    ("NG-KD", "Kaduna", [
        "Birnin Gwari", "Chikun", "Giwa", "Igabi", "Ikara", "Jaba",
        "Jema'a", "Kachia", "Kaduna North", "Kaduna South", "Kagarko",
        "Kajuru", "Kaura", "Kauru", "Kubau", "Kudan", "Lere", "Makarfi",
        "Sabon Gari", "Sanga", "Soba", "Zangon Kataf", "Zaria",
    ]),
    ("NG-KN", "Kano", [
        "Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi", "Bunkure",
        "Dala", "Dambatta", "Dawakin Kudu", "Dawakin Tofa", "Doguwa",
        "Fagge", "Gabasawa", "Garko", "Garun Mallam", "Gaya", "Gezawa",
        "Gwale", "Gwarzo", "Kabo", "Kano Municipal", "Karaye", "Kibiya",
        "Kiru", "Kumbotso", "Kunchi", "Kura", "Madobi", "Makoda",
        "Minjibir", "Nasarawa", "Rano", "Rimin Gado", "Rogo", "Shanono",
        "Sumaila", "Takai", "Tarauni", "Tofa", "Tsanyawa", "Tudun Wada",
        "Ungogo", "Warawa", "Wudil",
    ]),
    ("NG-KT", "Katsina", [
        "Bakori", "Batagarawa", "Batsari", "Baure", "Bindawa", "Charanchi",
        "Dan Musa", "Dandume", "Danja", "Daura", "Dutsi", "Dutsin Ma",
        "Faskari", "Funtua", "Ingawa", "Jibia", "Kafur", "Kaita", "Kankara",
        "Kankia", "Katsina", "Kurfi", "Kusada", "Mai'adua", "Malumfashi",
        "Mani", "Mashi", "Matazu", "Musawa", "Rimi", "Sabuwa", "Safana",
        "Sandamu", "Zango",
    ]),
    ("NG-KB", "Kebbi", [
        "Aleiro", "Arewa Dandi", "Argungu", "Augie", "Bagudo", "Birnin Kebbi",
        "Bunza", "Dandi", "Fakai", "Gwandu", "Jega", "Kalgo", "Koko/Besse",
        "Maiyama", "Ngaski", "Shanga", "Suru", "Wasagu/Danko", "Yauri", "Zuru",
    ]),
    ("NG-KO", "Kogi", [
        "Adavi", "Ajaokuta", "Ankpa", "Bassa", "Dekina", "Ibaji", "Idah",
        "Igalamela Odolu", "Ijumu", "Kabba/Bunu", "Kogi", "Lokoja",
        "Mopa Muro", "Ofu", "Ogori/Magongo", "Okehi", "Okene",
        "Olamaboro", "Omala", "Yagba East", "Yagba West",
    ]),
    ("NG-KW", "Kwara", [
        "Asa", "Baruten", "Edu", "Ekiti", "Ifelodun", "Ilorin East",
        "Ilorin South", "Ilorin West", "Irepodun", "Isin", "Kaiama",
        "Moro", "Offa", "Oke Ero", "Oyun", "Pategi",
    ]),
    ("NG-LA", "Lagos", [
        "Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa",
        "Badagry", "Epe", "Eti Osa", "Ibeju-Lekki", "Ifako-Ijaiye",
        "Ikeja", "Ikorodu", "Kosofe", "Lagos Island", "Lagos Mainland",
        "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere",
    ]),
    ("NG-NA", "Nasarawa", [
        "Akwanga", "Awe", "Doma", "Karu", "Keana", "Keffi", "Kokona",
        "Lafia", "Nasarawa", "Nasarawa Egon", "Obi", "Toto", "Wamba",
    ]),
    ("NG-NI", "Niger", [
        "Agaie", "Agwara", "Bida", "Borgu", "Bosso", "Chanchaga",
        "Edati", "Gbako", "Gurara", "Katcha", "Kontagora", "Lapai",
        "Lavun", "Magama", "Mariga", "Mashegu", "Mokwa", "Moya",
        "Paikoro", "Rafi", "Rijau", "Shiroro", "Suleja", "Tafa", "Wushishi",
    ]),
    ("NG-OG", "Ogun", [
        "Abeokuta North", "Abeokuta South", "Ado-Odo/Ota", "Egbado North",
        "Egbado South", "Ewekoro", "Ifo", "Ijebu East", "Ijebu North",
        "Ijebu North East", "Ijebu Ode", "Ikenne", "Imeko Afon",
        "Ipokia", "Obafemi Owode", "Odeda", "Odogbolu", "Ogun Waterside",
        "Remo North", "Shagamu",
    ]),
    ("NG-ON", "Ondo", [
        "Akoko North East", "Akoko North West", "Akoko South East",
        "Akoko South West", "Akure North", "Akure South", "Ese Odo",
        "Idanre", "Ifedore", "Ilaje", "Ile Oluji/Okeigbo", "Irele",
        "Odigbo", "Okitipupa", "Ondo East", "Ondo West", "Ose", "Owo",
    ]),
    ("NG-OS", "Osun", [
        "Atakumosa East", "Atakumosa West", "Aiyedaade", "Aiyedire",
        "Boluwaduro", "Boripe", "Ede North", "Ede South", "Egbedore",
        "Ejigbo", "Ife Central", "Ife East", "Ife North", "Ife South",
        "Ifedayo", "Ifelodun", "Ila", "Ilesa East", "Ilesa West",
        "Irepodun", "Irewole", "Isokan", "Iwo", "Obokun", "Odo Otin",
        "Ola Oluwa", "Olorunda", "Oriade", "Orolu", "Osogbo",
    ]),
    ("NG-OY", "Oyo", [
        "Afijio", "Akinyele", "Atiba", "Atisbo", "Egbeda", "Ibadan North",
        "Ibadan North East", "Ibadan North West", "Ibadan South East",
        "Ibadan South West", "Ibarapa Central", "Ibarapa East",
        "Ibarapa North", "Ido", "Irepo", "Iseyin", "Itesiwaju",
        "Iwajowa", "Kajola", "Lagelu", "Ogbomosho North", "Ogbomosho South",
        "Ogo Oluwa", "Olorunsogo", "Oluyole", "Ona Ara", "Orelope",
        "Ori Ire", "Oyo East", "Oyo West", "Saki East", "Saki West",
        "Surulere",
    ]),
    ("NG-PL", "Plateau", [
        "Barkin Ladi", "Bassa", "Bokkos", "Jos East", "Jos North",
        "Jos South", "Kanam", "Kanke", "Langtang North", "Langtang South",
        "Mangu", "Mikang", "Pankshin", "Qua'an Pan", "Riyom", "Shendam", "Wase",
    ]),
    ("NG-RI", "Rivers", [
        "Abua/Odual", "Ahoada East", "Ahoada West", "Akuku-Toru",
        "Andoni", "Asari-Toru", "Bonny", "Degema", "Eleme", "Emohua",
        "Etche", "Gokana", "Ikwerre", "Khana", "Obio/Akpor", "Ogba/Egbema/Ndoni",
        "Ogu/Bolo", "Okrika", "Omuma", "Opobo/Nkoro", "Oyigbo",
        "Port Harcourt", "Tai",
    ]),
    ("NG-SO", "Sokoto", [
        "Binji", "Bodinga", "Dange Shuni", "Gada", "Goronyo", "Gudu",
        "Gwadabawa", "Illela", "Isa", "Kebbe", "Kware", "Rabah",
        "Sabon Birni", "Shagari", "Silame", "Sokoto North", "Sokoto South",
        "Tambuwal", "Tangaza", "Tureta", "Wamako", "Wurno", "Yabo",
    ]),
    ("NG-TA", "Taraba", [
        "Ardo Kola", "Bali", "Donga", "Gashaka", "Gassol", "Ibi",
        "Jalingo", "Karim Lamido", "Kurmi", "Lau", "Sardauna",
        "Takum", "Ussa", "Wukari", "Yorro", "Zing",
    ]),
    ("NG-YO", "Yobe", [
        "Bade", "Bursari", "Damaturu", "Fika", "Fune", "Geidam",
        "Gujba", "Gulani", "Jakusko", "Karasuwa", "Machina", "Nangere",
        "Nguru", "Potiskum", "Tarmua", "Yunusari", "Yusufari",
    ]),
    ("NG-ZA", "Zamfara", [
        "Anka", "Bakura", "Birnin Magaji/Kiyaw", "Bukkuyum", "Bungudu",
        "Gummi", "Gusau", "Kaura Namoda", "Maradun", "Maru", "Shinkafi",
        "Talata Mafara", "Tsafe", "Zurmi",
    ]),
]

COUNTRY_ID = "NG"
COUNTRY_NAME = "Nigeria"


class Command(BaseCommand):
    help = "Seed Nigeria states and LGAs into the database (idempotent)."

    def handle(self, *args, **options):
        from accounts.models import Country, State, LGA

        self.stdout.write("Seeding locations...")

        with transaction.atomic():
            # Country — find by name (id may have been auto-assigned in an earlier seed)
            # On a fresh Render DB, id='NG' will be inserted cleanly.
            # On an existing DB where Nigeria was created with a different id,
            # we reuse that existing record to avoid the unique-name constraint.
            try:
                country = Country.objects.get(name=COUNTRY_NAME)
                self.stdout.write(f"  Country exists: {COUNTRY_NAME} (id={country.id})")
            except Country.DoesNotExist:
                country = Country.objects.create(id=COUNTRY_ID, name=COUNTRY_NAME)
                self.stdout.write(f"  Created country: {COUNTRY_NAME} (id={COUNTRY_ID})")

            states_created = 0
            lgas_created = 0

            for state_id, state_name, lga_names in NIGERIA_STATES:
                state, s_created = State.objects.get_or_create(
                    id=state_id,
                    defaults={"name": state_name, "country": country},
                )
                if s_created:
                    states_created += 1

                for i, lga_name in enumerate(lga_names, start=1):
                    lga_id = f"{state_id}-{i:02d}"
                    _, l_created = LGA.objects.get_or_create(
                        id=lga_id,
                        defaults={"name": lga_name, "state": state},
                    )
                    if l_created:
                        lgas_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {states_created} states, {lgas_created} LGAs created "
                f"({len(NIGERIA_STATES)} states, "
                f"{sum(len(l) for _, _, l in NIGERIA_STATES)} LGAs total in dataset)."
            )
        )
