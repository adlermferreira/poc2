opts = detectImportOptions('PedroChavesRadicals2.csv');
opts.VariableNamesLine = 1;
A = readtable("PedroChavesRadicals2.csv", opts);
A.Partido = [];
b = zeros(size(A,1)-1, 1);
tipos = A(2:283, 1049);
tipos = tipos{:, :};
A = A(2:283, 2:1049);
A = A{:, :};

for i = 1: size(A, 1)
    if tipos(i, 1) == 1
        b(i) = log(0.99999/(1 - 0.99999));
    else
        b(i) = log(0.00001/(1 - 0.00001));
    end
end

I = eye(size(A, 2));
alpha = (I + A.'*A)\(A.'*b); %alpha > 0, voto sim, alpha < 0 -> voto não
aux = A*alpha;
num = exp(aux);
p = num./(1 + num);

%votos_sim = find(tipos == 1);
%votos_nao = find(tipos == 0);
%plot([p(votos_sim)', p(votos_nao)'], 'o')

%[a, i] = sort(alpha, 'descend')
%Index dos maiores valores Sem a classe: 68 297 298 14 5
%Index dos menores valores Sem a classe: 527 142 41 109 210
%Index dos maiores valores Com a classe: 1048 201 528 334 987 235
%Index dos menores valores Com a classe: 553 192 527 3 1
plot(alpha, 'o')

