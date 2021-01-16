import pandas as pd
import numpy as np
import datetime


from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


#Plots functions 
import matplotlib.pyplot as plt
def get_pyplot(col,title,xlabel,ylabel,df):
    plt.figure(figsize=(30,10))

    for i in range(len(col)): 
        plt.plot(df.Dates, df[col[i]], label = col[i])

    plt.legend(loc='upper left',fontsize = 'xx-large')
    plt.xlabel(xlabel, fontsize = 25 )
    plt.ylabel(ylabel, fontsize = 25)
    plt.title (title,fontsize = 20)
    plt.xticks(fontsize = 20)
    plt.yticks(fontsize = 20)

    plt.show()
    
    
import plotly.graph_objects as go
def get_go_plotly(col,title,xlabel,ylabel,df):
    data = []
    for i in range(len(col)): 
        plot = go.Scatter(x=df.Dates,y=df[col[i]], name=col[i])
        data.append(plot)
    
    layout = go.Layout(title= title ,
                    xaxis=dict(title=xlabel),
                    yaxis=dict(title=ylabel ), 
                    width = 1000, 
                    height = 500, 
                    autosize = False)

    fig = go.Figure(data=data, layout=layout)

    fig.show()
    fig.write_image( title +".png")
     
def count_na(future):
    for col in future.columns.values:
        print(future[col].isna().value_counts())
        
        
        
        
#STEP1) Preprocess data 
def preprocess_future_data(filename,initial_investment, bid_ask):
    file = pd.read_excel(filename)
    features = file.columns.values
    px_names = [idx for idx in features if idx[0:7] == "PX_LAST"] 
    future_name = ["SPH","SPM","SPU","SPZ"]
    start_year = 0 
    end_year = 20
    years = ["%.2d" % i for i in range(start_year, end_year + 1)]


    index_names = []
    for i in years : 
        for j in future_name:
            index_names.append(j+i+" index")

    #check if len(index_names) == len(px_names)
    file.rename(columns=dict(zip(px_names, index_names)), inplace=True)

    file = file.fillna(method = "ffill")

    cols = [index_names[i] for i in range(len(index_names))]
    cols = ["Dates"] + cols
    Prices_file = file[cols]

    
    #Making date adjustments 
    file = Prices_file
    file["Dates"] = pd.to_datetime(file["Dates"])
    file = file.set_index(file["Dates"])
    file = file.drop(columns = {"Dates"})
    file.head(3)

    if "Unnamed: 0" in file.columns.values:
        file = file.drop(columns = {"Unnamed: 0"})
        
    return file

#STEP 2) Create the expiry schedule 

def create_expiry_schedule(file, roll_start_day):
    # Find the expiry date. 
    column = file.columns.values
    expiry = pd.DataFrame(columns = ["Expiry_date", "Future","Last_price", "roll_start_date"])

    start = 0 
    for col in column: 
        for i in range(start , len(file[col])):
            if i+2 == len(file) : 
                break 

            if file[col][i] == file[col][i+1] ==file[col][i+2]:
                future_value = (file[col][i-1])
                future = col
                date = file.index[i-1]
                roll_start_date = file.index[i-(roll_start_day + 1)]
                expiry = expiry.append({'Expiry_date': date, "Future" : col, "Last_price" : future_value
                                       , "roll_start_date" : roll_start_date }, ignore_index=True)
                start = i+1
                break

    if (set(column) - set(expiry.Future.values)):
        last_future_name = (set(column) - set(expiry.Future.values)).pop()

    expiry = expiry.append({'Expiry_date': file.index[len(file)-1], "Future" : last_future_name, 
                    "Last_price" : file.loc[file.index[len(file)-1],last_future_name]
                               , "roll_start_date" : file.index[len(file)-1] }, ignore_index=True)

    return expiry

def create_future_df(file,expiry):
    future = pd.DataFrame(columns = [ "Dates","Future", "Current Future", "Next Future", "Next Future current val", "Number of contracts","Contract Value"])
    future

    for i in range(len(expiry)):
        if i==0:
            temp = file[file.index < expiry["Expiry_date"][i]]
        else : 
            temp = file[(file.index < expiry["Expiry_date"][i]) & (file.index >= expiry["Expiry_date"][i-1])]
        value = expiry["Future"][i]
        for j in range(len(temp)):
            date = temp.index[j] 
            future = future.append({"Future":value, "Dates":date}, ignore_index=True)


    return future


def fill_future_current_value(future, file, expiry):

    list_futures = expiry["Future"]
    future["Next Future current val"] = 0 

    for i in range(len(future)-1):
        future.loc[i,"Current Future"] = file.loc[future["Dates"][i],future["Future"][i]]

        if future.loc[i,"Future"]==future["Future"][i+1]:
            future.loc[i,"Next Future"] = file.loc[future["Dates"][i],future["Future"][i]]
        else:
            future.loc[i,"Next Future"] = file.loc[future["Dates"][i],future["Future"][i+1]]


        #Adding for roll logic 
        curr = future["Future"][i]
        for j in range(len(list_futures)-1):
            if curr == list_futures[j]:
                next_fut = list_futures[j+1]
        future.loc[i,"Next Future current val"] = file.loc[future["Dates"][i],next_fut]
    return future 

def fill_future_contract_value(future, initial_investment, bid_ask):
    future.loc[0,"Number of contracts"] = initial_investment / (250*future.loc[0,"Current Future"])
    future.loc[0,"Contract Value"]= initial_investment


    for i in range(len(future)-1):
        if future.loc[i,"Future"] == future["Future"][i+1]: 
            future.loc[i+1,"Number of contracts"] = future["Number of contracts"][i]
        else:
            future.loc[i+1,"Number of contracts"] = future["Contract Value"][i]/(250*(future["Next Future"][i] + bid_ask))
        future.loc[i+1,"Contract Value"] = future["Number of contracts"][i+1] * future["Current Future"][i+1]*250

    future["Dates"] = pd.to_datetime(future["Dates"])
    return future 
    

def roll(roll_df,future, weights):
    roll_df = roll_df.reset_index()
    roll_df["roll_precent"] = pd.Series(weights)

    for i in range(len(roll_df)):
        if i==0:
            roll_df.loc[0,"Pre_roll_contracts"] = roll_df.loc[0,"Number of contracts"]
        else :
            roll_df.loc[i,"Pre_roll_contracts"] = roll_df.loc[i-1,"Post_roll_contracts"]

        roll_df.loc[i,"Contract_value_left"] = roll_df.loc[i,"Pre_roll_contracts"] * roll_df.loc[i,"Current Future"]
        roll_df.loc[i,"Rolled_value"] = roll_df.loc[i,"roll_precent"] * roll_df.loc[i,"Contract_value_left"]
        roll_df.loc[i,"Remaining_value"] = roll_df.loc[i,"Contract_value_left"] - roll_df.loc[i,"Rolled_value"]
        roll_df.loc[i,"New_contracts_rolled"] = roll_df.loc[i,"Rolled_value"]/roll_df.loc[i,"Next Future current val"]
        roll_df.loc[i,"Post_roll_contracts"] = roll_df.loc[i,"Remaining_value"]/roll_df.loc[i,"Current Future"]

        if i==0 :
            roll_df.loc[i,"Total_rolled_contracts"] = roll_df.loc[i,"New_contracts_rolled"]
        else:
            roll_df.loc[i,"Total_rolled_contracts"] = roll_df.loc[i-1,"Total_rolled_contracts"]+roll_df.loc[i,"New_contracts_rolled"]

        roll_df.loc[i,"Total_contract_vlaue"] = 250*(roll_df.loc[i,"Total_rolled_contracts"] * roll_df.loc[i,"Next Future current val"] + 
                                                    roll_df.loc[i,"Post_roll_contracts"] * roll_df.loc[i,"Current Future"])



    #Updating the contract value in the futures dataframe 
    for i in range(len(roll_df)):
        index = roll_df.loc[i,"index"]
        future.loc[index,"Contract Value"] = round(roll_df.loc[i,"Total_contract_vlaue"],10)
        
    
    
def annualization(year,month,day ,ann_freq, annual_table, spx_column, future_column):
    
    current_date = pd.Timestamp(year,month,day)
    date = current_date - datetime.timedelta(days=365*ann_freq)
    old_date = future.iloc[future.index.get_loc(date,method='ffill')].Dates

    returns_spx = ((future.loc[current_date,spx_column]/future.loc[old_date,spx_column])**(1/ann_freq)-1)
    returns_future = ((future.loc[current_date,future_column]/future.loc[old_date,future_column])**(1/ann_freq)-1)
    
    
    col = "annual_" + str(ann_freq)+ "_yrs"
    annual_table[col] = 0 
    annual_table.loc["Start Period",col] = old_date.strftime("%Y-%m-%d")
    annual_table.loc["End Period",col] = current_date.strftime("%Y-%m-%d")
    annual_table.loc["No.of yrs",col] = ann_freq
    annual_table.loc["No.of yrs",col] = ann_freq
    annual_table.loc["SPX return",col] = returns_spx
    annual_table.loc["Futures+Cash return",col] = returns_future
    annual_table.loc["Diff (bps)",col] = 10000* (annual_table[col]["Futures+Cash return"]- annual_table[col]["SPX return"])
    
    
def rolling_avg_returns(year,month,day ,ann_freq, annual_table, spx_column, future_column):
    
    current_date = pd.Timestamp(year,month,day)
    date = current_date - datetime.timedelta(days=365*ann_freq)
    old_date = future.iloc[future.index.get_loc(date,method='ffill')].Dates

    mean_spx = future[(future.index <= current_date) & (future.index >= old_date)][spx_column].mean()
    mean_future = future[(future.index <= current_date) & (future.index >= old_date)][future_column].mean()
    
    col = "Rolling Avg" + str(ann_freq)+ "_yrs"
    annual_table[col] = 0 
    annual_table.loc["Start Period",col] = old_date.strftime("%Y-%m-%d")
    annual_table.loc["End Period",col] = current_date.strftime("%Y-%m-%d")
    annual_table.loc["No.of yrs",col] = ann_freq
    annual_table.loc["No.of yrs",col] = ann_freq
    annual_table.loc["SPX return",col] = mean_spx
    annual_table.loc["Futures+Cash return",col] = mean_future
    annual_table.loc["Diff (bps)",col] = 10000* (annual_table[col]["Futures+Cash return"]- annual_table[col]["SPX return"])