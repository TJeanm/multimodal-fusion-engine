/*
 * Palette Graphique - prélude au projet multimodal 3A SRI
 * 4 objets gérés : cercle, rectangle(carré), losange et triangle
 * (c) 05/11/2019
 * Dernière révision : 28/04/2020
 */

import java.awt.Point;
import java.util.concurrent.ConcurrentLinkedQueue;
import fr.dgac.ivy.*;

ArrayList<Forme> formes; // liste de formes stockées
FSM mae; // Finite Sate Machine
int indice_forme;
PImage sketch_icon;

Ivy bus;
boolean fusionMode = true;

ConcurrentLinkedQueue<String[]> commandesIvy = new ConcurrentLinkedQueue<String[]>();
ConcurrentLinkedQueue<String[]> deplacementsIvy = new ConcurrentLinkedQueue<String[]>();

void setup() {
  size(800,600);
  surface.setResizable(true);
  surface.setTitle("Palette multimodale");
  surface.setLocation(20,20);
  sketch_icon = loadImage("Palette.jpg");
  surface.setIcon(sketch_icon);
  
  formes= new ArrayList(); // nous créons une liste vide
  noStroke();
  mae = FSM.INITIAL;
  try {
  bus = new Ivy("Palette", "Palette Ready", null);

  bus.bindMsg(
    "^Fusion Create=(cercle|rectangle|triangle|losange) X=([0-9]+) Y=([0-9]+)$",
    new IvyMessageListener() {
      public void receive(IvyClient client, String[] args) {
        commandesIvy.add(args.clone());
      }
    }
  );

  bus.bindMsg(
  "^Fusion Move Shape=(cercle|rectangle|triangle|losange|any) FromX=([0-9]+) FromY=([0-9]+) ToX=([0-9]+) ToY=([0-9]+)(?: Color=(rouge|vert|bleu))?$",
  new IvyMessageListener() {
    public void receive(IvyClient client, String[] args) {
      deplacementsIvy.add(args.clone());
    }
  }
);

  bus.start("127.255.255.255:2010");
  println("[IVY] Palette connectee au bus");

} catch (IvyException e) {
  println("[IVY] Erreur : " + e.getMessage());
}
  indice_forme = -1;
}

void draw() {
  
  background(0);
  traiterCommandesIvy();
  traiterDeplacementsIvy();
 // println("MAE : " + mae + " indice forme active ; " + indice_forme);
  switch (mae) {
    case INITIAL:  // Etat INITIAL
      background(255);
      fill(0);
      text("Etat initial (c(ercle)/l(osange)/r(ectangle)/t(riangle) pour créer la forme à la position courante)", 50,50);
      text("m(ove)+ click pour sélectionner un objet et click pour sa nouvelle position", 50,80);
      text("click sur un objet pour changer sa couleur de manière aléatoire", 50,110);
      break;
      
    case AFFICHER_FORMES:  // 
    case DEPLACER_FORMES_SELECTION: 
    case DEPLACER_FORMES_DESTINATION: 
      affiche();
      break;   
      
    default:
      break;
  }  
}

// fonction d'affichage des formes m
void affiche() {
  background(255);
  /* afficher tous les objets */
  for (int i=0;i<formes.size();i++) // on affiche les objets de la liste
    (formes.get(i)).update();
}

void mousePressed() {

  // Forward mouse clicks to the multimodal fusion engine
  if (fusionMode) {

    if (mouseButton != LEFT) {
      return;
    }

    String message = "Palette Click X=" + mouseX
                   + " Y=" + mouseY;

    try {
      if (bus != null) {
        bus.sendMsg(message);
        println("[IVY] Sent: " + message);
      }
    } catch (IvyException e) {
      println("[IVY] Error: " + e.getMessage());
    }

    return;
  }

  // Original palette behavior
  Point p = new Point(mouseX, mouseY);

  switch (mae) {
    case AFFICHER_FORMES:
      for (int i=0;i<formes.size();i++) { // we're trying every object in the list
        // println((formes.get(i)).isClicked(p));
        if ((formes.get(i)).isClicked(p)) {
          (formes.get(i)).setColor(color(random(0,255),random(0,255),random(0,255)));
        }
      } 
      break;
      
   case DEPLACER_FORMES_SELECTION:
     for (int i=0;i<formes.size();i++) { // we're trying every object in the list        
        if ((formes.get(i)).isClicked(p)) {
          indice_forme = i;
          mae = FSM.DEPLACER_FORMES_DESTINATION;
        }         
     }
     if (indice_forme == -1)
       mae= FSM.AFFICHER_FORMES;
     break;
     
   case DEPLACER_FORMES_DESTINATION:
     if (indice_forme !=-1)
       (formes.get(indice_forme)).setLocation(new Point(mouseX,mouseY));
     indice_forme=-1;
     mae=FSM.AFFICHER_FORMES;
     break;
     
    default:
      break;
  }
}


void keyPressed() {

  // Toggle between multimodal and local debug modes
  if (key == 'v' || key == 'V') {
    fusionMode = !fusionMode;

    println("[MODE] " + (fusionMode ? "Fusion" : "Debug"));
    return;
  }

  // Disable local keyboard actions in multimodal mode
  if (fusionMode) {
    return;
  }

  // Existing code below
  Point p = new Point(mouseX, mouseY);

  switch(key) {
      // ...
    case 'r':
      Forme f= new Rectangle(p);
      formes.add(f);
      mae=FSM.AFFICHER_FORMES;
      break;
      
    case 'c':
      Forme f2=new Cercle(p);
      formes.add(f2);
      mae=FSM.AFFICHER_FORMES;
      break;
    
    case 't':
      Forme f3=new Triangle(p);
      formes.add(f3);
       mae=FSM.AFFICHER_FORMES;
      break;  
      
    case 'l':
      Forme f4=new Losange(p);
      formes.add(f4);
      mae=FSM.AFFICHER_FORMES;
      break;    
      
    case 'm' : // move
      mae=FSM.DEPLACER_FORMES_SELECTION;
      break;
  }
}

void traiterCommandesIvy() {
  String[] args;

  while ((args = commandesIvy.poll()) != null) {

    String type = args[0];
    int x = Integer.parseInt(args[1]);
    int y = Integer.parseInt(args[2]);

    Point p = new Point(x, y);
    Forme f = null;

    if (type.equals("cercle")) {
      f = new Cercle(p);
    } else if (type.equals("rectangle")) {
      f = new Rectangle(p);
    } else if (type.equals("triangle")) {
      f = new Triangle(p);
    } else if (type.equals("losange")) {
      f = new Losange(p);
    }

    if (f != null) {
      formes.add(f);
      mae = FSM.AFFICHER_FORMES;

      println("[IVY] Forme creee : " + type +
              " (" + x + ", " + y + ")");
    }
  }
}


boolean correspondType(Forme f, String type) {
  if (type.equals("any")) return true;

  if (type.equals("cercle")) return f instanceof Cercle;
  if (type.equals("rectangle")) return f instanceof Rectangle;
  if (type.equals("triangle")) return f instanceof Triangle;
  if (type.equals("losange")) return f instanceof Losange;

  return false;
}


boolean correspondCouleur(Forme f, String couleur) {

  // No color filter: accept any object color.
  if (couleur == null || couleur.trim().isEmpty()) {
    return true;
  }

  if (couleur.equals("rouge"))
    return f.getColor() == color(255, 0, 0);

  if (couleur.equals("vert"))
    return f.getColor() == color(0, 255, 0);

  if (couleur.equals("bleu"))
    return f.getColor() == color(0, 0, 255);

  return false;
}

void traiterDeplacementsIvy() {
  String[] args;

  while ((args = deplacementsIvy.poll()) != null) {

    String type = args[0];

    int fromX = Integer.parseInt(args[1]);
    int fromY = Integer.parseInt(args[2]);
    int toX = Integer.parseInt(args[3]);
    int toY = Integer.parseInt(args[4]);

    String couleur = args.length > 5 ? args[5] : null;

    Point source = new Point(fromX, fromY);
    Point destination = new Point(toX, toY);

    ArrayList<Forme> candidates = new ArrayList<Forme>();

    for (Forme f : formes) {

      println("[DEBUG] Objet : " + f.getClass().getSimpleName());
      println("[DEBUG] Centre : "
              + f.getLocation().x + ", "
              + f.getLocation().y);

      println("[DEBUG] Clic source : "
              + fromX + ", " + fromY);

      println("[DEBUG] isClicked : " + f.isClicked(source));
      println("[DEBUG] Type OK : " + correspondType(f, type));
      println("[DEBUG] Couleur OK : " + correspondCouleur(f, couleur));

      if (!f.isClicked(source)) continue;
      if (!correspondType(f, type)) continue;
      if (!correspondCouleur(f, couleur)) continue;

      candidates.add(f);
    }

    // Never select an arbitrary object when the click is ambiguous.
    if (candidates.size() != 1) {
      println("[IVY] Deplacement refuse : "
            + candidates.size() + " objet(s) compatibles");
      continue;
    }

    Forme selection = candidates.get(0);

    selection.setLocation(destination);
    mae = FSM.AFFICHER_FORMES;

    println("[IVY] Forme deplacee : " + type
            + " (" + fromX + ", " + fromY + ")"
            + " -> (" + toX + ", " + toY + ")");
  }
}