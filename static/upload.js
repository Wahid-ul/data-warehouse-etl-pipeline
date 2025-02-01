$('#prev1').click(function(e){
    e.stopImmediatePropagation() ;
});

$('#button').click(function(e){
    e.preventDefault();
    //var form_data=new FormData($('#upload_file')[0]);
    let file = document.getElementById("upload_file").files[0];
    let form_data = new FormData();
    form_data.append("file", file);
    if(!file){
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("upload_error").innerHTML = "***can't upload an empty file!";
        return false;

    }else{
    //fetch('/upload', {method: "POST", body: formData});
    $.ajax({
        type:"POST",
        url:"/upload",
        data:form_data,
        contentType:false,
        catch:false,
        processData:false,
        success:function(result){
            if(result=="File uploaded successfully"){
                alert(result);
                console.log(result);
                //window.location.href="http://127.0.0.1:5000/dashboard";
                window.location.href="http://192.168.130.245:5000/table";
            }
            else if(result=="some files are missing!"){
                alert(result);
                e.stopImmediatePropagation;
                return false;
            }
            else if(result=="Files with same barcode are not found"){
                alert(result);
                e.stopImmediatePropagation;
                return false;
            }
            else if(result=="Error has occured"){
                alert(result);
                e.stopImmediatePropagation;
                return false;
            }
            
            
            //window.location.href="http://127.0.0.1:5000/dashboard";
        },
        error:function(error){
            console.log("error!");
        }

    });
    console.log(form_data);
}
                
});
