#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <string>
using namespace std;

int main(){
    ifstream numOfFiles("./data/fileCount.txt");
    string line;
    int partial_files = 0;
    if(numOfFiles.is_open()){
        while(getline(numOfFiles, line)){
            reverse(line.begin(), line.end());
            int product = 1;
            for(auto c : line){
                partial_files += product * (c - '0');
                product *= 10;
            }
        }
        numOfFiles.close();
    } 
    cout<<"partial_files : "<<partial_files<<"\n";
    vector<int> not_used(partial_files, 1);
    vector<vector<string> > file_data(partial_files);
    vector<ifstream> file_pointers(partial_files);
    // for(int i=0;i < partial_files;i++){
    //     string num = "";
    //     num += char(i + '0');
    //     ifstream descriptor("./data/index"+num+".txt");
    //     file_pointers[i] = descriptor;
    // }
     
    return 0;
}