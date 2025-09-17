# Kiro-mini API Documentation

This document provides comprehensive documentation for the Kiro-mini REST API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API uses basic authentication. In production, implement proper OAuth2 or JWT authentication.

```http
Authorization: Bearer <token>
```

## Content Types

All API endpoints accept and return JSON unless otherwise specified.

```http
Content-Type: application/json
Accept: application/json
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456"
}
```

### Common Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Study Management

### Ingest Study

Ingest a new study into the system.

```http
POST /studies/{study_uid}/ingest
```

**Parameters:**
- `study_uid` (path, required): Unique study identifier

**Request Body:**
```json
{
  "patient_id": "PAT001",
  "study_date": "2024-01-15",
  "modality": "US",
  "exam_type": "echo_complete",
  "study_description": "Complete Echocardiogram",
  "series_description": "Echo Series",
  "metadata": {
    "referring_physician": "Dr. Smith",
    "institution": "General Hospital"
  }
}
```

**Response:**
```json
{
  "study_uid": "1.2.3.4.5.6.7.8.9",
  "patient_id": "PAT001",
  "study_date": "2024-01-15",
  "modality": "US",
  "exam_type": "echo_complete",
  "status": "received",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get Study

Retrieve study information.

```http
GET /studies/{study_uid}
```

**Response:**
```json
{
  "study_uid": "1.2.3.4.5.6.7.8.9",
  "patient_id": "PAT001",
``2248000
`tamp: 164meso-Tih1...
X-Kir7c6d5e4f3g26=a8bture: sha25iro-Signa-K``http
X

`erification:es for vgnaturC-SHA256 si include HMAebhooksity

Wook Secur

### Webh
```
}"
  }008.1.1"192.16address": ,
    "ip_d_001"": "raider_   "us
 ata": {  "metad"
  },
01"rad_0id": logist_"radio   final",
 tatus": "   "s,
 7.8.9"3.4.5.6."1.2.d":  "study_ui3",
   t_12d": "rprt_i    "repodata": {
",
  ": "rpt_123source_id"  "reort",
ep_type": "Rresource00Z",
  "5T10:40:01-12024-mp": " "timesta
 nalized",.fi: "reportvent_type"  "evt_123",
nt_id": "eve"e`json
{
  
``Format
d k Payloabhoo# Weted

## comple/X12 exporteted` - FHIRort.compled
- `expratperbill generated` - Sugenebilling.lized
- `Report fina- lized` t.finaor `rept updated
-- Reporated` .upd- `reporteated
 crortew repted` - Nreport.crea ` updated
-metadata - Study y.updated`ted
- `stud ingesw study Ned` -study.createes

- `Typ
### Event nts:
ious evear vtions for notificaokports webho system sup
Thebhooks
``

## We5
  }
}
`": 2etious_offs"prev
    t": 75,"next_offse 
   ue,evious": tras_pr
    "hrue,: t"has_next" : 50,
     "offset"": 25,
  limit50,
    "": 1total"
    ": {tion
  "pagina: [...],"data"son
{
  

```jtadata:agination mee includes pRespons
=50
```
&offset=25udies?limit /stET
G```http

eters:amfset` par `oflimit` and `tion usingort paginas suppst endpointtion

Liagina``

## P
`2248000t: 164Limit-Rese 95
X-RateRemaining:RateLimit- 100
X-it-Limit:teLimRa
X-```https:

in responseluded s are inceaderlimit h
Rate user
er per minute pests **: 100 requnstioport opera
- **Ex per userinuteper msts 0 requetions**: 20ort operaer
- **Reper usute p per min requests: 50ance***AI assist
- *ute per IPests per min0 requ: 10**gestion*Study in
- *e:
fair usagensure ng to itilims rate PI implemente A
Th
ting# Rate Limi
#"
}
```
00Z0::1T1101-15 "2024-updated":t_ },
  "las
 on": trueidatie_valal_timree,
    "ru": ttions_ai_generab_10su  "true,
  gestion": s_in    "sub_5 true,
":e_workflowone_minut
    "ts": {gemance_tar"perfor
  },
  }
    2.1.0"sion": "vel_ver    "mod,
  vice:8080"//ai-sertp:ht"rl": ,
      "uconnected"": "   "status": {
   eai_servic"  },
    .12.0"
  sion": "1      "ver",
anc:8042/orthttp:/url": "h    "cted",
  "conne": status"
      hanc": {{
    "ortices": rnal_servxte  },
  "eue
": tronlidatiime_va "real_te,
    trusistance":ai_as
    "rue,": tbhooks "we  
 t": true,_expor"x12
    true,_export":     "fhires": {
pabilitica
  "0",: "1.0.version"",
  "ctives": "atatu_siongrat{
  "inte
**
```jsonse:spon

**Re```status
egration/GET /int
```httpilities.

apab candtus ion staratk integhecatus

Cation Sttegr### In

```
15
  }
}t": _percen"cpu_usage,
    _mb": 256ry_usage    "memo50,
_time_ms": sponse{
    "re: ance""perform
  },
  y""healthservice": i_  "athy",
  heal": "thanc   "or
 ealthy",s": "hredi
    "hy",ltse": "heaaba  "dat  {
ces": 
  "servi,.0""1.0ersion": 
  "v,00Z"T11:05:4-01-15": "202imestamphy",
  "thealtatus": "st
{
  "json
```:**ponsees
**R```
/health
ttp
GET 

```hh status.ealtstem hck sy
Che Check
theals

### Hystem Statu
## S}
```
Z"
15T11:00:00"2024-01-ed_at": 
  "generat   }
  },e": 0.12
 att_revision_r"repor  .98,
    cy_rate": 0cura"billing_ac94,
      ate": 0.curacy_r"ai_ac     ": {
 ty_metricsli
    "qua
    },1 seconds"": "2._timeationner_billing_geverage    "anutes",
  "25 mi": imen_tioort_createrage_rep   "av
   seconds",me": "8.5 ration_tii_geneverage_a"a
      onds",ec "3.2 s":tion_timeudy_ingesage_st "aver {
     etrics":formance_m    "per 0
    },
tions":rol_viola_cont  "access99,
    ": 0.reegrity_sco"data_int     ": true,
 s_logged_event
      "all": {_compliance"audit   },
    es"
 "45 minutme": ssing_tiroceage_p   "aver 0.97,
   ion_rate":et "compl
     ls": 145,ilrbotal_supe"t     48,
 orts": 1_rep  "total   150,
 dies": tal_stu "to    ry": {
  "summa",
   014-"202"date":    ,
 "month"period":   "": {
  ortmpliance_repn
{
  "co
```jsoonse:**t

**Respe repor thic date forifnt): Specfault: curreional, dete` (optdayear)
- ` month, week,ay, period (dt "): Reporhnt"moefault: (optional, d
- `period` *:* Parametersuery
```

**Qrtliance/repo/audit/comp
GET tpht

```port.pliance rerate a comneReport

Geliance ### Get Comp
```

0:00Z"
}5T16:3-12024-01: ""ivity"last_act
  ,14r": ty_hou"peak_activi,
    }ills": 2
   "superb,
 reports": 8
    "": 5,studie   "s
 cessed": {resources_ac
  },
  "E": 2ING_GENERATLL  "BI  
ALIZE": 3,EPORT_FIN"R
    E": 2,ATPORT_UPD"RE
    ": 3,EATEORT_CRREP,
    "SS": 5_ACCEUDY    "ST": {
ent_types  "ev15,
l_events": "tota
  },
  "3:59:59Z-01-15T2to": "2024
    "0Z",00:00:05T4-01-1m": "202ro: {
    "f"period",
  001"d_ "ra"user_id":
{
  **
```json*Response:
*
 dater to: Filtel)(optiona- `date_to` 
ateter from dilal): From` (option_fte- `daers:**
et Param

**Query`
``d}/activity/{user_i/audit/user
GET `httpuser.

``specific for a mary tivity sumGet acmary

vity Sumtit User Ac`

### Ge0
}
``offset": ,
  "00 1": "limit
 ": 1, "total,
   }
  ]   }
  "
   letempcho_co": "eexam_type   "    7.8.9",
 1.2.3.4.5.6.y_uid": "ud"st{
        : etadata"   "m:00Z",
   0:3515T14-01-202": "imestamp"t
      8.1.100",192.16ess": ""ip_addr    st",
  radiologi: ""role     "user_d_001",
 _id": "ra     "userpt_123",
  "r":e_idourc  "res",
    ortep"Re_type": resourc  "   ,
 6.7.8.9"2.3.4.5.dy 1.r stucreated fo: "Report "description   "event_
   ",ATERT_CRE": "REPOt_type    "even_001",
  udit": "a"log_id {
      gs": [
   t_lo
{
  "audi
```jsone:**esponsip

**Rr to skbeumt: 0): Nefaul(optional, d`offset` entries
- of 0): Number lt: 10nal, defau(optiot` 
- `limiter to datel): Filnae_to` (optio
- `dataterom d Filter fional):rom` (optte_f type
- `day resourceFilter bptional): (oe` _typce`resournt type
- ilter by evetional): Ftype` (op
- `event_r by userlteptional): Fi_id` (o- `userers:**
ramet
**Query Pail
```
/audit/tra``http
GET 

`ries.entudit trail eve aRetri

ailt Audit TrGence

### iapldit & Com

## Au
}
```0Z"10:57:02024-01-15Tat": "ent_ "s },
 ts": 1
 "attemp0,
     20me_ms":esponse_ti "r 200,
   de":"status_co
    ess": true,ucc    "sesult": {
tion_rica
  "notiff_789",id": "notiication_otif
  "non
{
```jse:**
**Respons```
r_001"
}
 "use"user_id":  ecret",
webhook_s "et_key":"secr
  ",.96.7.8"1.2.3.4.5.ource_id": "res",
  webhook.com/s://exampletpht"_url": ebhook,
  "wdy.created"tuype": "s"event_t",
  ": "study "type
 son
{
```j*dy:*Request Bo
**
```
ks/sendST /webhoo``http
PO

`cation.bhook notifisend a we

Manually cationk Notifihoo## Send Web

#0Z"
}
```-15T10:55:04-01202t": "ested_a"t,
  
  } truefied":verignature_  "si",
  ed\"}iv": \"recetatus\"sy": "{\odesponse_b"r150,
    time_ms": onse_   "resp0,
 e": 20"status_codrue,
     tess":ucc {
    "sesult":t_r,
  "tesk".com/webhooples://exam: "httpook_url"bh "we{
 json
``
`se:**
**Respon
rification veuregnatkey for sil): Secret ionaptcret_key` (oseto test
- `: URL ` (required)`webhook_url:**
- ersaramet*Query P

*t
```webhooks/tesp
POST /.

```httonfigurationint cndpo a webhook e

TestpointWebhook Endst  Tent

###meok Managebho

## We```"
}
:52:00Z24-01-15T10d_at": "20"validate },
  rue
 sent": tields_prequired_f"reA1",
    5010X222"00_version": format,
    "ant": trueompli "hipaa_ck": {
   pliance_checom  "c]
  },
"
    provided not d NM109 fielOptional
      "[ings": arn],
    "wrrors": [25,
    "ets":     "segmenets": 1,
n_snsactio "tra
   : true,alid"  "v  ation": {
  "valid6",
b_45: "sid"ll_
  "superbi
{**
```jsononse:**Resp
```

/validateperbill_id}sup/{837OST /x12/
P``httpaim.

`837P cl an X12 lidateVa 837P

X12## Validate 
#```

}
Z"15T10:50:00024-01-t": "2nerated_age
  "[]
  },"errors": ,
    ": 1on_sets "transactie,
    tru"valid":": {
    iondatali.",
  "v\n..X222A1\*0050107*0001A1\\nST*83010X222X*005*1*5*120000*2024011OUSELEARINGHNI*CIROMInGS*HC*K\\P*:0000001*0*00*00501**^40115*1200OUSE *2CLEARINGH      *ZZ*NIZ*KIROMI        *Z     *00*  0*     "ISA*0: "ontent
  "c2A1",22"005010Xon": si
  "ver2 837P",at": "X1  "form456",
": "sb_superbill_id
  "son
{```j
:**Response

**id}
```rbill_837p/{supe /x12/``http
GET.

`7P claim 83ll as X12t a superbiExpor
aim
837P Cl## Export xport

### X12 E
```


}  }
  ]      }
  AT001"
d": "P      "i
  "Patient",eType":   "resourc    {
  ": source    "re
    {
  }
    },"
      ": "rpt_123"id",
        icReport: "DiagnostType"urce    "resoe": {
     "resourc   {
         },
     }

  .5.6.7.8.9"3.4": "1.2."id    dy",
    gStuin"ImagrceType":     "resou
    e": {"resourc     {
   ": [
  "entry": 3,
  l
  "tota0Z",:45:001-15T10024-": "2estamp
  "timtion",": "collectype9",
  ".8..3.4.5.6.7e_1.2: "bundl
  "id"dle", "Bunype":esourceT{
  "r``json
e:**
`sponsces

**Reoner resour practitideclu): In: truefaultl, deer` (optionapractitione_lud `inc
-cent resouriede patIncluue): lt: tronal, defau` (optipatientinclude_ts
- `ic reporostagn Include dirue):, default: ts` (optionallude_report `incs:**
-y Parameter

**Quer
```_uid}udyndle/{stET /fhir/Buhttp
G

``` a study. forlete bundlea comp

Export xport Bundle

### E]
}
```
    }
    }
      ]      
        }1.3.1"
  1.4.1.08.5.1000.n:oid:1.2.84"urde":    "co    ",
     3986:ietf:rfc:"urnsystem":         "   
 ass": {   "sopCl       : 1,
  "number"        ,
.8.9.1.1".2.3.4.5.6.7d": "1"ui       {
       ": [
    stance"in   
   15,stances": rOfInmbe  "nu",
    Series"Echo ion": ipt"descr},
      "
      drasoun": "Ult"display,
        de": "US"        "coM",
ontology/DCsources/a.org/re/dicom.nem:/: "httpem""syst     {
    odality": "m 1,
     "number":      9.1",
6.7.8..5.: "1.2.3.4d"ui    "
   {[
   ": "series5,
  nces": 4tamberOfIns "nu": 3,
 eries"numberOfS0:00Z",
  5T10:3 "2024-01-1arted":,
  "st }"
 001ient/PATPat "rence":
    "refet": {ubjec  ],
  "s  }
sound"
  : "Ultralay" "dispS",
     "U: de"     "co,
 y/DCM"/ontologg/resourcesicom.nema.orhttp://dem": "     "syst [
    {
 lity":moda",
  "available": " "status
 .6.7.8.9",4.5": "1.2.3.y",
  "id"ImagingStud": sourceType  "ren
{
`jso**
``**Response:

}
```/{study_uidtudyImagingSGET /fhir/
```http
tudy.
gingSIR ImaFHy as tud a sExporty

ngStudgiort Ima

### Exp  ]
}
```
    }
   ]}
        ation"
   al examinurer preprocedor other funt": "Enco  "display    ",
    01.818": "Zcode        "-10",
  ir/sid/icd7.org/fh://hl"httpm":   "syste          {
     ing": [
   "cod     {
  ": [
 onCode  "conclusi,
ogram"ardiormal echocn": "Nlusio
  "conc
  ],"
    }_001/radionerctit": "Praference
      "re[
    {rformer": ",
  "pe0Z10:40:0024-01-15T": "2ssued"i:00Z",
  T10:3001-1524-: "20eDateTime"fectiv},
  "efAT001"
  ient/P": "Patreference{
    "bject":  },
  "su
    ]
 
      }udy"y straphiog: "Echocard"display"     
   "34552-0",": ode      "c",
  loinc.orgtp://m": "ht   "syste     {
  
    oding": ["c
    "code": { ],
   }
  ]
        }
  
      Radiology"": "lay "disp
         ",D"RA"code":           74",
m/v2-00Systeodeg/Cogy.hl7.orolttp://termin": "h "system    {
     
        "coding": [  {
      ry": [
   "categonal",
 "fiatus": 3",
  "strpt_12: ""
  "idort",sticRepagno: "DirceType"soure
  "
{**
```jsonponse:```

**Rest_id}
ort/{reporsticRep/Diagnohir /fttp
GET``h.

`osticReportiagns FHIR Deport art a rt

ExpoReporosticExport Diagn

### port
## FHIR Ex
```
w"
  }
}el": "lorisk_lev"    "high",
: nce"   "confide
 pproved",tatus": "a
    "sk": {e_feedbac  "immediat
": 0.94,_score "real_time0,
 ms": 15e_on_tim"validati,
  d": true{
  "vali`json
``**
se:espon
**R
```
"
}cardiogrammal echo"Norgs": findin,
  "mplete" "echo_coxam_type":8"],
  "e81s": ["Z01._coded10 "ic,
 93306"] ["_codes":
{
  "cpt
```json*t Body:*es

**Requime
```/realtatelidbilling/vahttp
POST /

```on.t creatiing repor-time durodes in reallidate cn

Va Validatio CodeReal-time``

### 0
}
`ime_ms": 80rocessing_t],
  "p
  lse
    }": fa   "primary 0.78,
   nce":de"confi
      oris", pectout anginary withry arteorona c nativeease oft distic hearlerooscAther "":on"descripti",
      "I25.10": d10_code "ic  {
     
  
    },e trurimary":    "p2,
   0.9e":onfidenc"c
      ation",mindural exaer preproceer for oth: "Encounttion"ripesc "d,
     .818"": "Z010_coded1ic{
      "": [
    stions  "sugge`json
{
:**
``
**Responseons
suggesti of umber: Nt: 5)nal, default` (optio
- `limiamf expe o): Tyirede` (requ- `exam_typtext
rt findings Repoired): ngs` (requ*
- `findiarameters:*y P
**Quer

```uggest/codes/sing
GET /bill.

```httpngs findied ons codes basd diagnosisuggesteGet AI-des

osis Cogest Diagn# Sug

##[]
}
```rnings": "wa
  ions": [],suggest
  },
  "0.95
    }ence": fid   "con    true,
ompatible":
      "cility": {compatibcode_",
     }
      }   ination"
edural examther preprocunter for onco": "Eiptiondescr"
        true,valid": "
        .818": {
      "Z01: {lidation"  "icd10_va
  },}
    
      50e": 185.sement_rateimbur   "r",
     ete complgraphy,Echocardioon": "escripti"d         true,
 "valid":{
       3306":      "9ion": {
 idat "cpt_vals": {
   _detailvalidationlow",
  ": "sk"bursement_riim "re95,
 ": 0.re_scocepliancom
  ": true,alid"n
{
  "v
```jsosponse:**

**Re`
``"
}ho_complete"ec: m_type",
  "exa818"]Z01.es": [""icd10_cod6"],
  s": ["9330odecpt_c
  "json
{y:**
```t BodReques`

**e
``alidat /billing/vhttp
POST
```ons.
atiode combin0 c-1PT and ICD Catealidodes

Vng Cidate Billi

### Val
```": true
}dated
  "vali0:45:00Z",-01-15T1at": "2024"created_
  pital",al Hoser"Genty_name": 
  "facili90",45678 "123":pi"provider_n
  85.50, 1arges":  "total_ch  }
  ],

  ary": true "prim",
     tionexaminal procedura preernter for oth "Encouption":cries,
      "d "Z01.818"":_codecd10"i  {
      es": [
  "diagnos}
  ],
  ": []
    odifiers "m     : 185.50,
"charge" 1,
      units":",
      "e completraphy,rdiog"Echocaption": ri"desc      ,
: "93306"de""cpt_co
       [
    {es":"servic ,
 
    }
  }23" "BC1_id":  "payer",
    ross: "Blue Cer_name"   "pay: {
   nce""insura",
    n St Maiss": "123addre",
    ": "M"gender"1",
    80-01-0 "19ob":    "dohn Doe",
ame": "J"n,
    T001"PA_id": "patient "  {
 ent_info": ti",
  "parpt_123_id": "
  "report"sb_456",ll_id":  "superbion
{
 se:**
```js
**Respon
}
}
```"
    }
  : "BC123ayer_id""p",
      ssBlue Crome": "payer_na      "ce": {
"insurant",
    "123 Main Sess":  "addr   ": "M",
r  "gende  ,
0-01-01": "198 "dob"oe",
   ": "John Dme{
    "na: "patient_info",
  "Hospitalral Genee": "namcility_",
  "fa90"12345678er_npi": vid,
  "propt_123"t_id": "r{
  "reporn
:**
```jsoody B

**Request```bills
T /super```http
POSort.

d repizefinalll from a rbisupeenerate a 
Gll
uperbinerate S Gent

###anageme Billing M}
```

##0
: 120"mssing_time_
  "proces": 0.89,ceconfidenment_hanceen.",
  " function..e and sizs normal inle appearght ventricts. The rin all segmenis normal imotion . Wall on of 65%tiacction fr with an ejec functionsystolie and  siztes normale demonstra ventriclhe left "Tdings":anced_fin"enhon
{
  e:**
```jsspons`

**Re
  }
}
``on": 65ction_fracti    "eje{
ents": asuremme"",
  plete"echo_comam_type": l",
  "exormars nrt appea: "Hea"findings"
{
  json**
```st Body:

**Reque```findings
nhance-OST /ai/e``http
PAI.

`th  findings wince existing
Enha Findings
nhance# E
##
```

}2100ime_ms": ng_tsies "proc": 0.91,
 enceconfid "overall_ },
 
    }
 falseormal": bn      "a.3 cm",
"3.9-5ange": ormal_r      "n,
ence": 0.88"confid
      ": "cm","unit   ,
   ": 4.8alue "v
      {n":ionstolic_dimer_end_diasculaentrift_v"le   },
    ": false
 "abnormal      ",
0%"55-7 mal_range":     "nor": 0.95,
 fidenceon,
      "c%"it": "    "un": 62,
  "value      ": {
ionfract_ejection_arulicntrleft_ve {
    "rements": "measujson
{
 onse:**
```Resp`

**}
``te"
cho_comple "e": "exam_type.7.8.9",
 .6 "1.2.3.4.5tudy_uid":
  "s{
json``
`** Body:
**Requestents
```
te-measuremi/genera
POST /a

```http using AI.ntse measuremeenerats

Gentasurem Generate Me###
```

}"v2.1.0"
": ersion  "model_vs": 3500,
sing_time_mproces "": 0.92,
 "confidence,
    }"93306"]
es": [d_cpt_cod"suggeste    
],18": ["Z01.8odes"diagnosis_csted_ugge"s",
    .endations..d recommAI-generate": "dations  "recommen..",
  pressions.generated imns": "AI-pressio   "im
    },
 
      }nce": 0.95   "confide%",
     "unit": "
        ue": 62,"val : {
       "ion_fraction_ejectricularventft_    "le
  ": {ements   "measur.",
 e analysis.. on imags basedindingated fner: "AI-gendings""fi {
   draft": report_on
{
  "
```jsesponse:***R
*
```
"
  }
}est painn": "Chatioinical_indic,
    "cl"M"nder": "patient_ge    e": 45,
tient_ag "pa
   ext": {
  "cont",ompleteho_c"ec pe":m_ty "exa7.8.9",
 .6..3.4.51.2 "uid": "study_``json
{
 :**
`Request Body``

**report
`i/assist-POST /a
```http
g AI.
t usin report draf
Generate a
tioneraReport GenI-Assisted 

### A Assistance

## AIr to skipumbe0): Nult: al, defat` (optionselts
- `offresuumber of : N0)efault: 5al, dit` (option
- `limo dater reports tte Fil (optional):date_to`
- `daterom orts fer rep: Filt(optional)_from` `datem type
- exar by lte Fi):onalype` (opti `exam_tl)
-t, finas (drafby statual): Filter s` (option
- `statugistdioloter by rational): Fil (opst_id`iologi
- `rad study UID: Filter bytional) (op `study_uid`:**
-rameters*Query Pa``

*
`/reportsT 
```http
GEltering.
onal fiith optireports w
List t Reports
### Lis
}
```

d_001"": "raized_by"final",
  :40:00ZT1001-15": "2024-ed_at  "finalizfinal",
us": ""stat_123",
  id": "rpt"report_`json
{
  
``onse:**Resp
```

**d}/finalizert_is/{repoOST /report``http
P.

`nal)draft to fitus from hanges sta (ce a report

FinalizportReze 
### Finali
```
ions"
}mendatecomdated r"Upons": ecommendati
  "ressions",dated improns": "Upsies
  "impr.",dings..pdated finngs": "U "findijson
{
 *
```Body:**Request ``

*id}
`rts/{report_PUT /repo`http

``orts).
draft repallowed for only ing report (istpdate an ex
Ueport
Update R
```

### 00Z"
}0:5T10:424-01-1d_at": "20  "finalize00Z",
38:T10:1-15 "2024-0at":updated_Z",
  "T10:35:0001-15 "2024-reated_at":l,
  "c": nulfidencei_conalse,
  "ad": fgenerateai_al",
  ": "fintus""sta6"],
  ": ["9330"cpt_codes8"],
  : ["Z01.81codes"gnosis_
  "diarequired",ow-up ": "No follndationscomme"reogram",
  cardirmal echo": "Noessions},
  "impr
    }
  ": false"abnormal      -70%",
: "55l_range""norma",
      "%  "unit": 65,
    "value":      n": {
 tiojection_fracentricular_e   "left_vents": {
   "measurem.",
unction.. systolic fe andnormal sizrates emonstle dleft ventricThe ndings": "",
  "fiho_completeype": "ecxam_t1",
  "e": "rad_00ist_idadiolog.9",
  "r.6.7.8.3.4.5 "1.2study_uid":
  "_123",d": "rpteport_i
  "rjson
{se:**
```

**Responid}
```eport_ts/{rporT /re
```http
GErt.
epo specific rrieve at

Ret## Get Repor`

#
}
``10:35:00Z"15T01-: "2024-at"d_reatee,
  "c falsated": "ai_gener"draft",
 ": "status6"],
  "9330": [odes,
  "cpt_cZ01.818"]["des": _co"diagnosis red",
 low-up requi": "No folionsndat"recomme,
  gram" echocardio"Normal: ressions""imp  }
  },
 false
    bnormal":"a",
      %: "55-70nge"ra  "normal_
    "%","unit": 65,
      value":   "
    tion": {jection_fracr_eulaft_ventric"le ts": {
   uremen
  "measction...",ic funstold sy annormal sizees nstrattricle demot venlefs": "The ding",
  "finho_completeype": "ec
  "exam_t",001 "rad_st_id":radiologi,
  ".8.9"4.5.6.71.2.3.": "study_uid  "_123",
 "rptrt_id":{
  "repo``json
*
`onse:*

**Resp```
}
"]"93306codes": [cpt_ ""],
 18": ["Z01.8codess_gnosiia",
  "duired reqow-upo foll": "Nndations"recommeam",
  echocardiogrl ": "Normaionsess
  "impr}
  },
    al": false    "abnorm  ",
 "55-70%_range":ormal  "n%",
    it": "     "un 65,
 alue":     "v {
 ion":acton_frlar_ejectientricu"left_v
    ements": {
  "measur",tion...ystolic funcand sl size maortrates nicle demonsntrleft ve": "The "findingsete",
  ho_compl: "ecpe""exam_ty",
  "rad_001": logist_id
  "radio8.9",.5.6.7..3.4 "1.2_uid":dy
{
  "stu**
```jsonuest Body:```

**Reqts
porrePOST /
```http
.
ort repology a new radi
Create Report
# Create
##t
gemenort Mana## Rep``

]
}
`}
     40:00Z"
 -15T10:0124-: "20nalized_at""fi",
      0Z15T10:35:02024-01-": "atated_"cre ",
     nal"fius":    "stat1",
    "rad_00ist_id":radiolog   "123",
   "rpt_port_id": re{
      "   s": [
 rt
  "repo.6.7.8.9",.2.3.4.5"1id": tudy_u
{
  "s``jsonsponse:**
`*Re

*ts
```}/reporstudy_uidstudies/{T /GE
```http

udy. st aeports forll rrts

Get aStudy Repo
### Get ``

`": 0
}"offset0,
  "limit": 5,
  ": 1tal,
  "to  ] }
ted"
   "complestatus":     "  mplete",
"echo_co":  "exam_type   ,
  "US"odality":  "m",
     -152024-01": ""study_date 
     T001",PAd": "patient_i   "
   8.9",4.5.6.7.": "1.2.3.y_uidstud
      "    {
": [dies
  "stu`json
{se:**
``pon**Resto skip

ults mber of res Nuefault: 0):(optional, dffset` n
- `olts to returesuumber of r Nefault: 50):al, dion (opt- `limit`Y-MM-DD)
YY (Y to dateer studiesnal): Filt(optiodate_to` DD)
- `Y-MM- date (YYYstudies fromer ): Filtional (opt_from`atetatus
- `d by sFilter): s` (optionalpe
- `statum tyr by exaal): Filteype` (option`exam_tlity
- modater by Filnal): y` (optioalitt ID
- `modby patien Filter l):nad` (optiotient_ipaers:**
- `aramet**Query P`

es
``GET /studi
```http
iltering.
onal fptidies with ostu
List 
udiesStt 
### Lis

  }
}
```": 45tance_count
    "ins": 3,nts_cou   "serie: {
 metadata"  "",
T10:35:00Z024-01-15d_at": "2date",
  "up0:00Z:34-01-15T10 "202at":d_eate
  "cr",leted": "comp
  "statusram",diogocarchmplete Etion": "Co_descrip
  "studye",ho_complet "ec":"exam_type  : "US",
modality",
  """2024-01-15: e"y_dat  "stud