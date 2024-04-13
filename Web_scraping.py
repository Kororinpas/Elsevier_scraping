from playwright.async_api import async_playwright
import asyncio
import nest_asyncio
import os
import pandas as pd
import traceback
from lxml import etree


### extract the data from paper page
def extract_page(html,df,element,failed_url):
    tree = etree.HTML(html)
    sur_name = tree.xpath('//*[@id="author-group"]/button/span/span/span[@class="text surname"]/text()')
    given_name = tree.xpath('//*[@id="author-group"]/button/span/span/span[@class="given-name"]/text()')
    if sur_name and given_name == []:
        name ="None"
    else:
        name = [x+" "+ y for x,y in zip(sur_name,given_name)]
        name = ','.join(name)
    institution = tree.xpath('//*[@id="author-group"]/dl/dd/text()')
    if institution == []:
        institution = "None"
    else:
        institution = ','.join(institution)
    publish_date = tree.xpath('//*[@id="banner"]/div[1]/p/text()')
    if publish_date == []:
        publish_date = "None"
    else:
        publish_date = ",".join(publish_date)
    doi = tree.xpath('//*[@id="article-identifier-links"]/a[@class="anchor doi anchor-default anchor-external-link"]/span/text()')
    if doi == []:
        doi = "None"
    else:
        doi = doi[0]
    cite = tree.xpath('//*[@id="citing-articles-header"]/h2/text()')
    if cite == []:
        cite = ["None"]
    else:
        cite = cite[0]
    abstract = tree.xpath('//*[@id="abstracts"]/div/div/p/text()')
    if abstract == []:
        abstract = tree.xpath('//*[@id="abstracts"]/div/div/p/span/text()')
        if abstract == []:
            abstract = "None"
        else:
            abstract = "====".join(abstract)
    else:
        abstract = "====".join(abstract)
    introduction = tree.xpath('//*[@class="Introduction u-font-gulliver text-s u-margin-l-ver"]/section/p/text()')
    if introduction == []:
        introduction = tree.xpath('//*[@class="Body u-font-gulliver text-s"]/div/section[1]/p/text()')
        if introduction == []:
            introduction = tree.xpath('//*[@class = "Abstracts u-font-gulliver text-s"]/div[@class="abstract author-highlights"]/div/p/ul/li/span/text()')
            if introduction == []:
                introduction = "None"
            else:
                introduction = "====".join(introduction)
        else:
            introduction = "====".join(introduction)
    else:
        introduction = "====".join(introduction)

    paper_info = {"name":name,"institution":institution,"publish_date":publish_date,"doi":doi,"cite":cite,"abstract":abstract,"introduction":introduction}
    paper_info.update(element)
    if paper_info["name"] == "None" or paper_info["institution"] == "None" or paper_info["publish_date"] == "None":
        failed_url.append({"Url":element["Url"],"Reason":"No author or institution or publish_date"}.update(paper_info))
    else:
        new_row = pd.DataFrame(paper_info, index=[0])
        new_df = pd.concat([df,new_row],ignore_index=True)
    
    return new_df,failed_url


## The whole process of scraping the detail information of each paper
async def detail_Elsver(page_url,df,element,failed_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = False,slow_mo=1500)
        
        ##创建独立环境
        context = await browser.new_context()
        page = await context.new_page()
        
        #增加反爬机制
        await page.add_init_script(
            """
                Object.defineProperties(navigator, {
                    webdriver:{
                        get:()=>undefined
                    }
                });
            """
        )
        retries = 0 
        max_retry = 10
        while retries < max_retry:
            try:
                await page.goto(page_url)
                await page.wait_for_load_state('networkidle',timeout=5000)
                await page.locator("button", has_text = "Show more").wait_for()
                await page.locator("button", has_text = "Show more").click()
                await page.wait_for_load_state('networkidle',timeout=5000)
                html = await page.content()
                new_df,failed_url= extract_page(html,df,element,failed_url)
                await browser.close()
                break
            except TimeoutError:
                retries += 1
                print('retrying...')
                await asyncio.sleep(5)
                continue
        return new_df,failed_url


import os 
import pandas as pd
from asyncio import InvalidStateError
import time

### main function
async def main():
    root_path = os.getcwd()
    basic_information_path = os.join(root_path,"basic_information")
    dataset_path = os.join(root_path,"dataset")
    os.chdir(basic_information_path)
    file_list = os.listdir()

    for x in file_list[14:]:
        ##读取文件，获得所有行的字典格式
        df = pd.read_csv(x)
        df = df.drop(columns=['Unnamed: 0.1'])
        df_list = df.to_dict("records")
        #转换到保存目录
        os.chdir(dataset_path)
        file_name = x.split(".")[0]
        if not os.path.exists(file_name):
            os.mkdir(file_name)
            os.chdir(file_name)
        else:
            os.chdir(file_name)
        ### 保存failed_url
        failed_url = []
        #创建新df
        new_df = pd.DataFrame(columns=["name","institution","publish_date","doi","cite","abstract","introduction","Title","Url","Time","Year","Type"])
        for element in df_list:
            Url = element["Url"]
            retries = 0
            max_retry = 10
            while retries < max_retry:
                try:
                    new_df,failed_url = await detail_Elsver(Url,new_df,element,failed_url)
                    break
                except InvalidStateError as e:
                    retries += 1
                    print('Chrome retrying...')
                    continue
                except UnboundLocalError as e:
                    retries += 2
                    print('UnboundLocalError retrying...')
                    continue
                except Exception as e:
                    failed_url.append({"Url":Url,"Error":e})
                    print(e)
                    break
        with open("failed_url.txt","w") as f:
            for line in failed_url:
                f.write(str(line))
                f.write("\n")

        again_failed_url = []
        if failed_url != []:
            for failure in failed_url:
                if failure != None and "Reason" in failure.keys():
                    if failure["Reason"] == "No author or institution or publish_date":
                        Url = failure["Url"]
                        new_df,again_failed_url = await detail_Elsver(Url,new_df,element,again_failed_url)

        with open("again_failed_url.txt","w") as f:
            for line in failed_url:
                f.write(str(line))
                f.write("\n")

        new_df.to_csv(x,index=False)
        os.chdir(basic_information_path)
        time.sleep(300)


asyncio.run(main())
    

