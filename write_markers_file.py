import pathlib
from ome_types import from_tiff
import argparse
import pandas as pd
import numpy as np

#CLI
def get_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--input_img',
                        required=True,
                        type=pathlib.Path,
                        help='absolute path of the input image stack (.tif)'
                        )
    
    parser.add_argument('-o',
                        '--output_dir',
                        required=True,
                        type=pathlib.Path,
                        help='absolute path of the directory where the output .csv file will be written'
                        )
    
    parser.add_argument('-fn',
                        '--output_file_name',
                        required=False,
                        type=str,
                        default="markers.csv",
                        help='name of the csv file'
                        )

    
    args=parser.parse_args()
    return args

def assign_background(df):
    #Create column ["backsub_process"] indicating which rows will be processed with backsub
    filters_=df.Filter.unique().tolist()
    regex=[rf"*{element}*" for element in filters_]
    backsub_process=df["marker_name"].replace(filters_,value=False,regex=True)
    backsub_process=np.where(backsub_process==False,False,True)
    df.insert(df.shape[1],"backsub_process",backsub_process)

    #Assign the latest mention of the autofluorescence channel to the correspondent row in the background column
    rename_background=[]
    for idx,row in df.iterrows():

        if row.backsub_process:
            previous_channels=reversed(df.iloc[:idx].marker_name.to_list())
            for element in previous_channels:
                #Supposes background name is a subset of the channel/marker name
                if row.background in element:
                    rename_background.append(element)
                    break
        else: 
            rename_background.append(None)
    df.drop(columns=["backsub_process"],inplace=True)
    df.background=rename_background

    return df



def main():
    args=get_args()
    img_path=args.input_img
    out_dir=args.output_dir
    file_name=args.output_file_name
    #Fetch metadata object
    ome=from_tiff(img_path)
    #Fetch image attributes from ome
    ch_names  = [ element.name for element in ome.images[0].pixels.channels ]
    exp_times = [ element.exposure_time for element in ome.images[0].pixels.planes ]
    #cycles=[int(element.attributes["CycleID"])+1 for element in ome.structured_annotations[0].value.any_elements[0].children]
    filters= [ element.attributes["FluorescenceChannel"] for element in ome.structured_annotations[0].value.any_elements[0].children ]
    background=[None if "DAPI" in element else element for element in filters]

    aux_dict={"channel_number":list(range(1,len(ch_names)+1)),
              #"cycle_number":cycles,
              "marker_name":ch_names,
              "Filter":filters,
              "background":background,
              "exposure":exp_times
              }
    df=pd.DataFrame(aux_dict)
    df_updated=assign_background(df)
    df_updated.to_csv( out_dir/file_name ,index=False)

if __name__ == '__main__':
    main()



    

