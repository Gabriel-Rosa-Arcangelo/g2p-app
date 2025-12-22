library(seqinr)
library(reticulate)
library(RSelenium)
library(Biostrings)
library(stringr)
library(dplyr)
library(purrr)
require(RJSONIO)

folder='/mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO'

if(grepl(".fas",list.files(paste0(folder,"/ANALISAR")))){
  cmd=paste0("python3 /home/catg/Scripts/HIV_Genotype/hiv_genotype/Geno2Pheno_Tropismo/fas_to_fasta.py ",folder,"/ANALISAR")
  system(cmd)
}else{
  print("No .fas files detected")
}

fasta_files=list.files(paste0(folder,'/ANALISAR/'), ".fasta", recursive = F, full.names = T)

fasta_files=unique(fasta_files)
print(fasta_files)

retrieve_pleres_data=function(temp_file='temp_pleres.txt',folder='/home/catg/Scripts/HIV_Genotype/hiv_genotype/Geno2Pheno_Tropismo/',n_weeks=150,desired_samples){
  desired_samples=gsub('\\..*$','',gsub('_.*','',gsub('.*/','',desired_samples)))
  desired_samples=desired_samples[!grepl('CN|CP|BRANCO|barcodes|NA',desired_samples)]
  desired_samples=paste("'",gsub('^0*','',unique(desired_samples)),"'",collapse=',',sep='')
  system(gsub('-','',paste0('python3 ',folder,'pleres_sysgeno_recipiente.py ','"',desired_samples,'"', ' ',folder,temp_file)))
  data=read.table(paste0(folder,temp_file),sep="\t",row.names=1,header=TRUE,quote="\"",comment.char = "",stringsAsFactors=FALSE)
  data
}

desired_samples=gsub(".fasta","",gsub('^0*','',gsub("_.*","",gsub(".*/","",fasta_files))))

pleres_data=retrieve_pleres_data(desired_samples=desired_samples)
pleres_data=pleres_data[grepl("V3120_MS",pleres_data[,6]),]

docker=system("docker ps", inter=T)
check=unlist(str_split(docker, '"'))[2]

if(grepl("selenium/standalone-firefox-debug:2.53.1", check)==TRUE){
  print("Docker is running fine my friend")
  docker_id=gsub(" ","",gsub("selenium/standalone-firefox-debug:2.53.1","",unlist(str_split(system("docker ps", inter=T),'"'))))[2]
}else{
  system('docker run -d -v /mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO:/tmp/mozilla_seluser0 -p 4445:4444 -p 5901:5900 selenium/standalone-firefox-debug:2.53.1')
  docker_id=gsub(" ","",gsub("selenium/standalone-firefox-debug:2.53.1","",unlist(str_split(system("docker ps", inter=T),'"'))))[2]
}


system(paste0("for i in ls ",folder,"/*.fasta; do awk '/^>/{if(N)exit;++N;} {print;}' $i > tmp && mv tmp $i; done"))
dir_docker="/tmp/mozilla_seluser0"
dir_pdf = "/mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO/ANALISAR/mozilla_seluser1/"

url="https://coreceptor.geno2pheno.org/"
name_xpath='//*[@id="g2pmain"]/div/center/table/tbody/tr[1]/td/input'
fpr_xpath='//*[@id="g2pmain"]/div/center/table/tbody/tr[5]/td/select/option[10]'
seq_css_selector='#g2pmain > div > center > table > tbody > tr:nth-child(8) > td > input[type=file]'
go_xpath='//*[@id="XactionCell"]/input'
pdf_css_selector='#g2pmain > div > table.navBar > tbody > tr > td.navTab > input[type=submit]'
csv_xpath='//*[@id="g2pmain"]/div/table[1]/tbody/tr/td[4]/input'


fprof <- makeFirefoxProfile(list(browser.download.dir = "/tmp/mozilla_seluser0",
                                 browser.download.folderList = 2L,
                                 browser.download.manager.showWhenStarting = F,
                                 browser.helperApps.neverAsk.saveToDisk =  "application/pdf"))

remDr <- remoteDriver(browserName = "firefox",remoteServerAddr = "localhost",port = 4445L,extraCapabilities = fprof)


get_geno2pheno_results = function(fasta_files){
  
  #Modulo principal (subtipo, nome da amostra, frase e seq)
  
  print("Opening Server")
  remDr$open(silent = T)
  print("Connecting to Geno2Pheno")
  remDr$navigate(url)
  
  print("Naming samples")
  name_link = remDr$findElement(using = "xpath", value = name_xpath)
  name_link$sendKeysToElement(list(gsub(".fasta","",gsub(".*/","",fasta_files))))
  print("Defining FPR")
  fpr_link = remDr$findElement(using = "xpath", value = fpr_xpath)
  fpr_link$clickElement()
  print("Loading Sequences")
  seq_link=remDr$findElement("css selector", seq_css_selector)
  seq_link$sendKeysToElement(list(paste0(dir_docker,gsub('.*/','/ANALISAR/',fasta_files))))
  print("Run Analysis")
  go_link = remDr$findElement('xpath',go_xpath)
  go_link$clickElement()
  go_link$screenshot(display = T)
  print("Get PDF")
  pdf_link=remDr$findElement('css selector',pdf_css_selector )
  pdf_link$clickElement()
  Sys.sleep(1)
  system(paste0("docker cp ",docker_id,":/tmp/mozilla_seluser1/ /mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO/ANALISAR"))
  file.rename(paste0(dir_pdf,"/",list.files(dir_pdf,".part", recursive =T)),paste0(dir_pdf,"/",gsub(".*/","",gsub("_consensus.fasta","",fasta_files)),".pdf"))
  
  system(paste0('echo "genomas" | sudo -S mv /mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO/ANALISAR/mozilla_seluser1/* /mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO/ANALISAR'))
  system(paste0('echo "genomas" | sudo -S rm -r /mnt/share/Doencas_Infecciosas/Doencas_Infecciosas_Storage/MINISTERIO_DA_SAUDE_ST/DADOS_BRUTOS/TROPISMO/ANALISAR/mozilla_seluser1'))
  system(paste0("docker exec ",docker_id," bash -c 'rm /tmp/mozilla_seluser1/*.part'"))
  
 
  sample=remDr$findElement('xpath','//*[@id="g2pmain"]/div/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td')
  sample=sample$getElementText()
  subtype=remDr$findElement('xpath','//*[@id="g2pmain"]/div/table[2]/tbody/tr[1]/td/table/tbody/tr[5]/td')
  subtype=subtype$getElementText()
  med=remDr$findElement('xpath','//*[@id="g2pmain"]/div/table[2]/tbody/tr[4]/td/table/tbody/tr[2]/td[2]')
  med=med$getElementText()
  fpr=remDr$findElement('xpath','//*[@id="g2pmain"]/div/table[2]/tbody/tr[4]/td/table/tbody/tr[2]/td[3]/center')
  fpr=fpr$getElementText()
  
  fasta=readDNAStringSet(fasta_files)
  fasta_name=names(fasta)
  teste=data.frame(Sample=as.character(sample), Subtype=as.character(subtype),
                   Phrase=as.character(med),FPR=as.character(fpr),Sequence=paste0(fasta),fasta_name=fasta_name,stringsAsFactors = F)
  file = list.files(paste0(folder,'/ANALISAR'), full.names = T, pattern = '.pdf')
  sample = gsub('.fasta.pdf','',gsub('.*/','',file))  
  system(paste0('mkdir -p ',folder,"/RESULTADOS/",Sys.Date(),'/',sample))
  system(paste0('mv ', folder,'/ANALISAR/*',sample,'* ',folder,"/RESULTADOS/",Sys.Date(),'/',sample))
  print("Closing Server")
  remDr$close()
  
  remDr$open(silent = T)
  print("Connecting to Geno2Pheno Mutext")
  remDr$navigate("https://bioinf.mpi-inf.mpg.de/apex/f?p=2001:8")
  remDr$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "xpath", value ='//*[@id="B1861320711414522"]/span')$clickElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "xpath", value ='//*[@id="P7_REFSEQ_SET"]/option[1]')$clickElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "xpath", value ='//*[@id="P7_REF_SEQS"]/option[6]')$clickElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "css selector", value ='#B3950511621674168 > span')$clickElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "xpath", value ='//*[@id="P8_NT_SEQ"]')$clearElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  seq=remDr$findElement(using = "xpath", value ='//*[@id="P8_NT_SEQ"]')
  Sys.sleep(2)
  seq$sendKeysToElement(list(paste0(fasta)))
  seq$screenshot(display = T)
  Sys.sleep(2)
  remDr$findElement(using = "xpath", value ='//*[@id="B1860502286414521"]/span')$clickElement()
  remDr$screenshot(display = T)
  Sys.sleep(2)
  text <- remDr$findElement(using = 'xpath', value = '//*[@id="P8_MUTATIONS_1"]')
  Sys.sleep(2)
  mut=text$getElementText()
  Sys.sleep(2)
  del=remDr$findElement(using = 'xpath', value ='//*[@id="P8_DELETIONS_1"]')
  Sys.sleep(2)
  del=del$getElementText()
  Sys.sleep(2)
  ins=remDr$findElement(using = 'xpath', value ='//*[@id="P8_INSERTIONS_1"]')
  Sys.sleep(2)
  ins=ins$getElementText()
  
  a=paste0(unlist(str_split(mut,",")))
  a=gsub(" ","",a)
  index=as.numeric(gsub('[A-Z]([0-9]*).*','\\1',a))
  
  k=NULL
  v=NULL
  fn=NULL
  for (i in seq_along(index)){
    k[i]=index[i]+28
    v[i]=gsub("   "," ",gsub("[[:digit:]]", " ",a[i]))
    fn[i]=gsub(" ", k[i],v[i])
    fn
  }
  
  
  index=as.numeric(gsub('[A-Z]([0-9]*).*','\\1',fn))%in%300:335
  a=fn[index]
  ##################### 
  
  index=as.numeric(gsub("\\D","",unlist(str_split(del,","))))
  
  k=NULL
  v=NULL
  fn=NULL
  for (i in seq_along(index)){
    k[i]=index[i]+28
    k[i]=paste0("del",k[i])
  }
  k
  b=k
  index=as.numeric(gsub('[a-z]([0-9]*)','\\1',b))%in%300:335
  b=b[index]
  ####################################
  
  
  c=paste0(gsub("([0-9])([A-Z])","\\1ins\\2",unlist(str_split(ins,","))))
  index=as.numeric(gsub("\\D","",unlist(str_split(ins,","))))
  
  k=NULL
  v=NULL
  fn=NULL
  for (i in seq_along(index)){
    k[i]=index[i]+28
    v[i]=gsub("   "," ",gsub("[[:digit:]]", " ",c[i]))
    fn[i]=gsub(" ", k[i],v[i])
    fn
  }
  
  index=as.numeric(gsub('[A-Za-z]([0-9]*)','\\1',fn))%in%300:335
  c=fn[index] 
  
  
  #  c=paste0(gsub("([0-9])([A-Z])","\\1ins\\2",unlist(str_split(ins,","))))
  #  index=as.numeric(gsub('[A-Za-z]([0-9]*)','\\1',c))%in%300:335
  #  c=c[index]
  
  
  all_mut=c(a,b,c)
  
  vals <- as.numeric(gsub("\\D","", all_mut))
  all_mut=all_mut[order(vals)]
  
  t=t(as.data.frame(all_mut))
  v=data.frame(teste,t,stringsAsFactors = F)
  remDr$close()
  
  teste$Sample=gsub('.fasta','',teste$Sample)
  write.csv(v,paste0(folder,"/RESULTADOS/",Sys.Date(),'/',sample,'/',teste$Sample,".db.csv"), row.names = F)
  v
}

try({base::do.call(dplyr::bind_rows,lapply(fasta_files, possibly(get_geno2pheno_results,NA)))},silent=TRUE)

db_files=list.files(paste0(folder,'/RESULTADOS'),pattern = ".csv", full.names = T, recursive=T)

out= do.call(bind_rows,lapply(db_files, function(x){
  read.table(x, sep = ',', header =T,stringsAsFactors = F,colClasses = c("character"))
}))

out[,3]=ifelse(grepl("Only",out[,3]), "R5 - O antagonista de CCR5 pode ser administrado.",
               'Tropismo pelo CXCR4 - O antagonista de CCR5 não deve ser administrado.')

out[,1]=gsub("^0*","",out[,1])


samples=gsub(".fasta","",gsub(".*/","",fasta_files))
print(samples)
pleres_data=retrieve_pleres_data(desired_samples=samples)
out$Sample=gsub(".fasta","",out$Sample)
mut_list_conc=apply( out[ , 7:length(out), drop=F ] , 1 , paste , collapse = " " )
mut_list_conc_2=data.frame(out, MUT = cbind(mut_list_conc))
mut_list_conc_2$mut_list_conc=gsub("NA","",mut_list_conc_2$mut_list_conc)
mut_list_conc_2$software_version = "Geno2pheno [coreceptor] 3.4"
mut_list_conc_2$software_access_date = paste0(Sys.Date())
mut_list_conc_2$lab_responsible = "Leandro Ucela Alves, Gerente Técnico e Científico, CRBio:072584/01-D (SP)"
mut_list_conc_2$lab_liberation = "Jaqueline de Souza Cavalcanti, Especialista em genotipagem, CRBio 56973/01-D (SP)"
mut_list_conc_2$analysis_methodology = "Geno2pheno"
sql_final=merge(mut_list_conc_2, pleres_data, by.x = "Sample",by.y = "IdRecipiente")

names(sql_final)[names(sql_final) == 'controle'] <- 'sisgeno_number'
names(sql_final)[names(sql_final) == 'Sequence'] <- 'consensus'
names(sql_final)[names(sql_final) == 'Sample'] <- 'sample_name'
names(sql_final)[names(sql_final) == 'analysis_methodology'] <- 'genotype_algorithm'

sql_final=sql_final[c("sisgeno_number",
                      "fasta_name",
                      "lab_responsible",
                      "lab_liberation",
                      "genotype_algorithm",
                      "software_access_date",
                      "software_version",
                      "consensus","FPR","Subtype","Phrase", "mut_list_conc")]


colnames(sql_final)[2]= 'sample_name'
sql_final=sql_final[c(1,2,5:7,9:12)]

fasta=list.files(paste0(folder,'/RESULTADOS/',Sys.Date()), pattern = '.fasta', recursive = T, full.names = T)
fasta_1 = fasta[!grepl( "pdf", fasta)]
if(nchar(gsub(".fasta","",gsub(".*/","",fasta_1)))!=12){
  lapply(fasta, function(x){
    dir=gsub("/[^/]+$", "", x)
    sample=gsub(".*/","",x)
    file.copy(x,paste0(dir,"/00000",sample))
    system(paste0("rm ",x))
  })
}


lapply(fasta[!grepl( "pdf", fasta)], function(x){
  out=pleres_data[grepl(paste0(gsub("^0*","",gsub(".fasta","",gsub("_.*","",gsub(".*/","",x))))),pleres_data$IdRecipiente),]
  sample = out$IdRecipiente
  while (12-nchar(sample)!=0) {
    sample=paste0('0',sample)
  }
  ifelse(nchar(sample)!=12,paste0('00000',sample),print("ok"))
  fasta=read.fasta(x,seqtype='DNA',as.string=TRUE)
  recipiente=out$controle
  write.fasta(sequences=toupper(fasta),names=paste0(recipiente,'_29SP_3'),
              file.out=paste0(folder,'/RESULTADOS/',Sys.Date(),'/',sample,'/',recipiente,'_29SP_3.fasta'),
              open='a')
  system(paste0('rm ',x))
  
})

lapply(fasta[grepl( "pdf", fasta)], function(x){
  out=pleres_data[grepl(paste0(gsub("^0*","",(gsub('.pdf','',gsub(".fasta","",gsub("_.*","",gsub(".*/","",x))))))),pleres_data$IdRecipiente),]
  recipiente=out$controle
  file.rename(x, paste0(gsub("/[^/]*$",'',x),'/',recipiente,'_29SP_3.pdf'))
})

csv=list.files(paste0(folder,'/RESULTADOS/', Sys.Date()), pattern = '.csv', recursive = T, full.names = T)

lapply(csv, function(x){
  out=pleres_data[grepl(paste0(gsub("^0*","",(gsub('.db','',gsub(".csv","",gsub("_.*","",gsub(".*/","",x))))))),pleres_data$IdRecipiente),]
  recipiente=out$controle
  file.rename(x, paste0(gsub("/[^/]*$",'',x),'/',recipiente,'_29SP_3.csv'))
})


file_2=list.files(paste0(folder,'/RESULTADOS/', Sys.Date()), full.names = T, pattern = ".pdf", recursive = T)
for (i in 1:length(file_2)) {
out=sql_final[grepl(paste0(gsub("^0*","",(gsub('.pdf','',gsub(".fasta","",gsub("_.*","",gsub(".*/","",file_2[i]))))))),sql_final$sisgeno_number),]
txt = out$mut_list_conc
txt=sub("(([[:alpha:]][^[:alpha:]]*){40})", "\\1\n ", txt)
print(system(paste0("python3 /home/catg/Scripts/HIV_Genotype/hiv_genotype/Geno2Pheno_Tropismo/rename_rel.py ",file_2[i]," '",txt,"'")))
}
