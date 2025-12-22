function mostrarSenha(){
    var inputPass = document.getElementById('id_password')
    var btnShowPass = document.getElementById('btn-eye')

    if(inputPass.type === 'password'){
        inputPass.setAttribute('type','text')
        btnShowPass.classList.replace('fa-eye','fa-eye-slash')
    }else{
        inputPass.setAttribute('type','password')
        btnShowPass.classList.replace('fa-eye-slash','fa-eye')
    }
}    